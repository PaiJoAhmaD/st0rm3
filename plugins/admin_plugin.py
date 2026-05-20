#===istalismanplugin===
# -*- coding: utf-8 -*-

import asyncio
import json
import time
import threading

def popups_check(bot, gch):
    cfg = bot.gch_config(gch)
    if 'popups' in cfg:
        return cfg['popups'] == 1
    cfg['popups'] = 1
    bot.save_gch_config(gch, cfg)
    return 1

def handler_remote(mtype, source, parameters):
    bot = handler_remote.bot
    groupchat = source[1]
    nick = source[2]
    groupchats = sorted(bot.groupchats.keys())

    if parameters:
        parts = parameters.split(' ', 2)
        dest_gch = parts[0]
        if len(parts) < 2:
            bot.reply(mtype, source, 'Invalid syntax!')
            return

        dest_comm = parts[1]
        dest_params = parts[2] if len(parts) > 2 else ''

        if dest_gch.isdigit():
            idx = int(dest_gch) - 1
            if 0 <= idx < len(groupchats):
                dest_gch = groupchats[idx]
            else:
                bot.reply(mtype, source, 'The Conference does not exist!')
                return
        elif dest_gch not in groupchats:
            bot.reply(mtype, source, 'The Conference does not exist!')
            return

        bot_nick = bot.get_bot_nick(dest_gch)
        dest_source = [f'{groupchat}/{nick}', dest_gch, bot_nick]

        cmd_lower = dest_comm.lower()
        if cmd_lower in bot.command_handlers:
            comm_handler = bot.command_handlers[cmd_lower]
        elif (bot.macrolist.get(dest_gch) and cmd_lower in bot.macrolist[dest_gch]):
            exp_alias = bot.macrolist[dest_gch][cmd_lower]
            alias_parts = exp_alias.split(' ', 1)
            dest_comm = alias_parts[0]
            alias_params = alias_parts[1] if len(alias_parts) > 1 else ''
            dest_params = (alias_params + ' ' + dest_params).strip()
            if dest_comm.lower() in bot.command_handlers:
                comm_handler = bot.command_handlers[dest_comm.lower()]
            else:
                bot.reply(mtype, source, 'Unknown command!')
                return
        elif hasattr(bot, 'gmacrolist') and cmd_lower in bot.gmacrolist:
            exp_alias = bot.gmacrolist[cmd_lower]
            alias_parts = exp_alias.split(' ', 1)
            dest_comm = alias_parts[0]
            alias_params = alias_parts[1] if len(alias_parts) > 1 else ''
            dest_params = (alias_params + ' ' + dest_params).strip()
            if dest_comm.lower() in bot.command_handlers:
                comm_handler = bot.command_handlers[dest_comm.lower()]
            else:
                bot.reply(mtype, source, 'Unknown command!')
                return
        else:
            bot.reply(mtype, source, 'Unknown command!')
            return

        if mtype == 'public':
            bot.reply(mtype, source, 'Look in private!')
        threading.Thread(
            target=asyncio.run,
            args=(comm_handler('private', dest_source, dest_params),)
        ).start()
    else:
        if groupchats:
            rep = 'Available Conferences:\n' + '\n'.join(
                f'{i+1}) {x}' for i, x in enumerate(groupchats)
            )
        else:
            rep = 'No available conferences!'
        bot.reply(mtype, source, rep)

def handler_redirect(mtype, source, parameters):
    bot = handler_redirect.bot
    groupchat = source[1]
    nick = source[2]

    if parameters and ':' in parameters:
        spltdp = parameters.split(':', 1)
        dest_nick = spltdp[0]
        if len(spltdp) < 2:
            bot.reply(mtype, source, 'Invalid syntax!')
            return
        mess = spltdp[1]
        comm_par = mess.strip().split(' ', 1)
        comm = comm_par[0]
        params = comm_par[1] if len(comm_par) > 1 else ''

        bot_nick = bot.get_bot_nick(groupchat)
        dest_source = [f'{groupchat}/{dest_nick}', groupchat, bot_nick]

        cmd_lower = comm.lower()
        if cmd_lower in bot.command_handlers:
            comm_handler = bot.command_handlers[cmd_lower]
        elif (bot.macrolist.get(groupchat) and cmd_lower in bot.macrolist[groupchat]):
            exp_alias = bot.macrolist[groupchat][cmd_lower]
            alias_parts = exp_alias.split(' ', 1)
            comm = alias_parts[0]
            alias_params = alias_parts[1] if len(alias_parts) > 1 else ''
            params = (alias_params + ' ' + params).strip()
            if comm.lower() in bot.command_handlers:
                comm_handler = bot.command_handlers[comm.lower()]
            else:
                bot.reply('private', dest_source, mess)
                bot.reply(mtype, source, 'Sent!')
                return
        elif hasattr(bot, 'gmacrolist') and cmd_lower in bot.gmacrolist:
            exp_alias = bot.gmacrolist[cmd_lower]
            alias_parts = exp_alias.split(' ', 1)
            comm = alias_parts[0]
            alias_params = alias_parts[1] if len(alias_parts) > 1 else ''
            params = (alias_params + ' ' + params).strip()
            if comm.lower() in bot.command_handlers:
                comm_handler = bot.command_handlers[comm.lower()]
            else:
                bot.reply('private', dest_source, mess)
                bot.reply(mtype, source, 'Sent!')
                return
        else:
            bot.reply('private', dest_source, mess)
            bot.reply(mtype, source, 'Sent!')
            return

        threading.Thread(
            target=asyncio.run,
            args=(comm_handler('private', dest_source, params),)
        ).start()
        bot.reply(mtype, source, 'Sent!')
    else:
        bot.reply(mtype, source, 'Invalid syntax!')

def handler_admin_join(mtype, source, parameters):
    bot = handler_admin_join.bot
    if source[1] not in bot.groupchats:
        source[2] = source[1].split('@')[0]

    if parameters:
        args = parameters.split()
        if not (args[0].count('@') and args[0].count('.') >= 1):
            bot.reply(mtype, source, 'read "help join"')
            return

        groupchat = args[0]
        passw = None
        reason = ''

        if len(args) > 1:
            if 'pass=' in args[1]:
                pass_str = args[1]
                pass_parts = pass_str.split('pass=', 1)
                if pass_parts[0] == '':
                    passw = pass_parts[1]
                    reason = ' '.join(args[2:])
                else:
                    reason = ' '.join(args[1:])
            else:
                reason = ' '.join(args[1:])

        for process in bot.stage1_init:
            threading.Thread(target=process, args=(groupchat,)).start()

        bot.join_room(groupchat, bot.default_nick, passw)
        bot.reply(mtype, source, 'join to ' + groupchat)
    else:
        bot.reply(mtype, source, 'read "help join"')

def handler_admin_leave(mtype, source, parameters):
    bot = handler_admin_leave.bot
    if source[1] not in bot.groupchats:
        source[2] = source[1].split('@')[0]

    args = parameters.split()
    if not args:
        if source[1] in bot.groupchats:
            groupchat = source[1]
            reason = ''
        else:
            bot.reply(mtype, source, 'this command only possible in the conference')
            return
    else:
        level = bot.user_level(f'{source[1]}/{source[2]}', source[1])
        if level < 40 and args[0] != source[1]:
            bot.reply(mtype, source, 'not allowed')
            return
        if args[0] not in bot.groupchats:
            bot.reply(mtype, source, 'i am not there')
            return
        groupchat = args[0]
        reason = ' '.join(args[1:]) if len(args) > 1 else ''

    bot.leave_room(groupchat, reason)
    bot.reply(mtype, source, 'leaved ' + groupchat)

def handler_admin_msg(mtype, source, parameters):
    bot = handler_admin_msg.bot
    if not parameters:
        bot.reply(mtype, source, 'read "help message"')
        return
    parts = parameters.split()
    if len(parts) < 2:
        bot.reply(mtype, source, 'Need recipient and message')
        return
    target = parts[0]
    body = ' '.join(parts[1:])
    bot.send_msg(target, body, mtype='chat')
    bot.reply(mtype, source, 'message sent')

def handler_glob_msg_help(mtype, source, parameters):
    bot = handler_glob_msg_help.bot
    total = 0
    totalblock = 0
    if bot.groupchats:
        for room in bot.groupchats:
            if popups_check(bot, room):
                bot.send_msg(room, f'News from {source[2]}:\n{parameters}\n... (help info) ...')
                totalblock += 1
            total += 1
        bot.reply(mtype, source, f'message sent to {totalblock} conference (from {total})')
    else:
        bot.reply(mtype, source, 'read "help hglobmsg"')

def handler_glob_msg(mtype, source, parameters):
    bot = handler_glob_msg.bot
    total = 0
    totalblock = 0
    if parameters and bot.groupchats:
        for room in bot.groupchats:
            if popups_check(bot, room):
                bot.send_msg(room, f'News from {source[2]}:\n{parameters}')
                totalblock += 1
            total += 1
        bot.reply(mtype, source, f'message sent to {totalblock} conference (from {total})')
    else:
        bot.reply(mtype, source, 'read "help globmsg"')

def handler_admin_say(mtype, source, parameters):
    bot = handler_admin_say.bot
    if parameters:
        bot.send_msg(source[1], parameters)
    else:
        bot.reply(mtype, source, 'read "help say"')

def handler_admin_restart(mtype, source, parameters):
    bot = handler_admin_restart.bot
    if source[1] not in bot.groupchats:
        source[2] = source[1].split('@')[0]
    reason = parameters or ''

    pres = bot.make_presence(pshow='unavailable')
    if reason:
        pres['status'] = f'{source[2]}: restarted me -> {reason}'
    else:
        pres['status'] = f'{source[2]}: restarted me'
    bot.send(pres)
    time.sleep(1)
    bot.disconnect()

def handler_admin_exit(mtype, source, parameters):
    bot = handler_admin_exit.bot
    if source[1] not in bot.groupchats:
        source[2] = source[1].split('@')[0]
    reason = parameters or ''

    pres = bot.make_presence(pshow='unavailable')
    if reason:
        pres['status'] = f'{source[2]}: shut me down -> {reason}'
    else:
        pres['status'] = f'{source[2]}: shut me down'
    bot.send(pres)
    time.sleep(2)
    import os
    os._exit(0)

def handler_popups_onoff(mtype, source, parameters):
    bot = handler_popups_onoff.bot
    if source[1] not in bot.groupchats:
        bot.reply(mtype, source, 'this command only possible in conference')
        return

    cfg = bot.gch_config(source[1])
    if parameters:
        try:
            val = int(parameters.strip())
        except ValueError:
            bot.reply(mtype, source, 'read "help popups"')
            return
        cfg['popups'] = val
        bot.save_gch_config(source[1], cfg)
        if val == 1:
            bot.reply(mtype, source, 'global notifications are turned on')
        else:
            bot.reply(mtype, source, 'global notifications are turned off')
    else:
        ison = cfg.get('popups', 1)
        if ison == 1:
            bot.reply(mtype, source, 'global notifications are turned on here')
        else:
            bot.reply(mtype, source, 'global notifications are turned off here')

def handler_botautoaway_onoff(mtype, source, parameters):
    bot = handler_botautoaway_onoff.bot
    if source[1] not in bot.groupchats:
        bot.reply(mtype, source, 'this command only possible in the conference')
        return

    cfg = bot.gch_config(source[1])
    if parameters:
        try:
            val = int(parameters.strip())
        except ValueError:
            bot.reply(mtype, source, 'read "help autoaway"')
            return
        cfg['autoaway'] = val
        bot.save_gch_config(source[1], cfg)
        if val == 1:
            bot.reply(mtype, source, 'auto-status enabled')
        else:
            bot.reply(mtype, source, 'auto-status disabled')
        get_autoaway_state(bot, source[1])
    else:
        ison = cfg.get('autoaway', 0)
        if ison == 1:
            bot.reply(mtype, source, 'auto-status is enable here')
        else:
            bot.reply(mtype, source, 'auto-status is disable here')

def get_autoaway_state(bot, gch):
    if 'autoaway' not in bot.gch_config(gch):
        bot.gch_config(gch)['autoaway'] = 0
    if bot.gch_config(gch)['autoaway']:
        bot.last['gch'][gch]['autoaway'] = 1
        bot.last['gch'][gch]['thr'] = None

def setup(bot):
    handler_remote.bot = bot
    handler_redirect.bot = bot
    handler_admin_join.bot = bot
    handler_admin_leave.bot = bot
    handler_admin_msg.bot = bot
    handler_glob_msg.bot = bot
    handler_glob_msg_help.bot = bot
    handler_admin_say.bot = bot
    handler_admin_restart.bot = bot
    handler_admin_exit.bot = bot
    handler_popups_onoff.bot = bot
    handler_botautoaway_onoff.bot = bot

    bot.register_command(
        handler_admin_join, 'join', access=100,
        desc='Join conference...', syntax='join <conf> [pass=12345] [reason]',
        examples=['join room@conference.server.tld', 'join room@conference.server.tld *VICTORY*'],
        category=['superadmin', 'muc', 'all']
    )
    bot.register_command(
        handler_admin_leave, 'leave', access=30,
        desc='Leave conference.', syntax='leave <conference> [reason]',
        examples=['leave room@conference.server.tld sleep', 'leave'],
        category=['admin', 'muc', 'all']
    )
    bot.register_command(
        handler_admin_msg, 'message', access=40,
        desc='Send message on behalf of bot.', syntax='message <jid> <message>',
        examples=['message guy@server.tld how are you?'],
        category=['admin', 'muc', 'all']
    )
    bot.register_command(
        handler_admin_say, 'say', access=20,
        desc='Talk through bot.', syntax='say <message>',
        examples=['say *HI* peoples'],
        category=['admin', 'muc', 'all']
    )
    bot.register_command(
        handler_admin_restart, 'restart', access=100,
        desc='Restart bot.', syntax='restart [reason]',
        examples=['restart refreshing'],
        category=['superadmin', 'all']
    )
    bot.register_command(
        handler_admin_exit, 'exit', access=100,
        desc='Shutdown bot.', syntax='exit [reason]',
        examples=['exit fixing bug'],
        category=['superadmin', 'all']
    )
    bot.register_command(
        handler_glob_msg, 'globmsg', access=100,
        desc='Send news to all conferences.', syntax='globmsg [message]',
        examples=['globmsg hi all!'],
        category=['superadmin', 'muc', 'all']
    )
    bot.register_command(
        handler_glob_msg_help, 'hglobmsg', access=100,
        desc='Send news with help reminder.', syntax='globmsg [message]',
        examples=['hglobmsg read help'],
        category=['superadmin', 'muc', 'all']
    )
    bot.register_command(
        handler_popups_onoff, 'popups', access=30,
        desc='Turn on/off popups in current room.', syntax='popups [1|0]',
        examples=['popups 1', 'popups'],
        category=['admin', 'muc', 'all']
    )
    bot.register_command(
        handler_remote, 'remote', access=40,
        desc='Remote execute command in other room.', syntax='remote <room> <command> [params]',
        examples=['remote botzone@conference.jsmart.web.id ping guy', 'remote'],
        category=['superadmin', 'muc', 'all']
    )
    bot.register_command(
        handler_redirect, 'redirect', access=20,
        desc='Redirect command result to user privately.', syntax='redirect <nick>:<command>|<mess>',
        examples=['redirect guy: ping lady'],
        category=['admin', 'muc', 'all']
    )

    bot.stage1_init.append(lambda gch: get_autoaway_state(bot, gch))