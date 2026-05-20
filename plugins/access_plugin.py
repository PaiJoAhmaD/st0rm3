#===istalismanplugin===
# -*- coding: utf-8 -*-

import json

def handler_access_login(mtype, source, parameters):
    bot = handler_access_login.bot
    if mtype == 'public':
        bot.reply(mtype, source, 'Stupid, this command had to perform in the private!!! ]:->')
        return
    jid = bot.get_true_jid(source)
    if parameters.strip() == bot.admin_password:
        bot.globaccess[jid] = 100
        bot.save_globaccess()
        bot.reply('private', source, 'Global full access granted')
    else:
        bot.reply('private', source, 'Incorrect password')

def handler_access_logout(mtype, source, parameters):
    bot = handler_access_logout.bot
    jid = bot.get_true_jid(source)
    if jid in bot.globaccess:
        del bot.globaccess[jid]
        bot.save_globaccess()
    bot.reply(mtype, source, 'Access withdrawn')

def handler_access_view_access(mtype, source, parameters):
    bot = handler_access_view_access.bot
    accdesc = {
        '-100': '(full ignored)', '-1': '(blocked)', '0': '(none)',
        '1': '(poor member :D )', '10': '(user)', '11': '(member)',
        '15': '(moder)', '16': '(moder)', '20': '(admin)',
        '30': '(owner)', '40': '(pionir)', '100': '(bot admin)'
    }
    room = source[1]
    if not parameters:
        level = str(bot.user_level(source, room))
        levdesc = accdesc.get(level, '')
        bot.reply(mtype, source, f'{level} {levdesc}')
    else:
        if room not in bot.groupchats:
            bot.reply(mtype, source, 'This is only possible in the conference')
            return
        nick = parameters.strip()
        if nick in bot.groupchats.get(room, {}) and bot.groupchats[room][nick].get('ishere'):
            jid = bot.groupchats[room][nick]['jid']
            level = str(bot.user_level(jid, room))
            levdesc = accdesc.get(level, '')
            bot.reply(mtype, source, f'{level} {levdesc}')
        else:
            bot.reply(mtype, source, 'where is the guy? :-O')

def handler_access_set_access(mtype, source, parameters):
    bot = handler_access_set_access.bot
    room = source[1]
    if room not in bot.groupchats:
        bot.reply(mtype, source, 'This is only possible in the conference')
        return
    splitdata = parameters.split()
    if len(splitdata) < 1:
        bot.reply(mtype, source, 'wrong command, read "help set_access"')
        return
    if len(splitdata) > 1:
        try:
            level = int(splitdata[1])
        except ValueError:
            bot.reply(mtype, source, 'wrong command, read "help set_access"')
            return
        if level > 100 or level < -100:
            bot.reply(mtype, source, 'wrong command, read "help set_access"')
            return
    nick = splitdata[0].strip()
    if nick not in bot.groupchats.get(room, {}) or not bot.groupchats[room][nick].get('ishere'):
        bot.reply(mtype, source, 'where is the guy? :-O')
        return
    target_jid = bot.groupchats[room][nick]['jid']
    target_bare = target_jid.split('/')[0] if '/' in target_jid else target_jid
    source_bare = bot.get_true_jid(source)
    jidacc = bot.user_level(source_bare, room)
    toacc = bot.user_level(target_bare, room)

    if source_bare not in bot.admins:
        if target_bare == source_bare:
            if len(splitdata) > 1 and level > jidacc:
                bot.reply(mtype, source, ':-P')
                return
        else:
            if toacc > jidacc:
                bot.reply(mtype, source, ':-P')
                return
            if len(splitdata) > 1 and level >= jidacc:
                bot.reply(mtype, source, ':-P')
                return

    if len(splitdata) == 1:
        bot.change_access_perm(room, target_bare)
        if nick == source[2]:
            bot.reply(mtype, source, 'local access withdrawn, need to rejoin room')
        else:
            bot.reply(mtype, source, f'local access withdrawn, {nick}, need to rejoin room')
    elif len(splitdata) == 2:
        bot.change_access_temp(room, target_bare, level)
        bot.reply(mtype, source, 'local temporary access granted')
    elif len(splitdata) == 3:
        bot.change_access_perm(room, target_bare, level)
        bot.reply(mtype, source, 'local permanent access granted')
    else:
        bot.reply(mtype, source, 'wrong command, read "help set_access"')

def handler_access_set_access_glob(mtype, source, parameters):
    bot = handler_access_set_access_glob.bot
    room = source[1]
    if room not in bot.groupchats:
        bot.reply(mtype, source, 'This is only possible in the conference')
        return
    if not parameters:
        bot.reply(mtype, source, 'eee?')
        return
    splitdata = parameters.strip().split()
    if len(splitdata) < 1 or len(splitdata) > 2:
        bot.reply(mtype, source, 'eee?')
        return
    nick = splitdata[0].strip()
    if nick not in bot.groupchats.get(room, {}) or not bot.groupchats[room][nick].get('ishere'):
        bot.reply(mtype, source, 'where is the guy? :-O')
        return
    target_jid = bot.groupchats[room][nick]['jid']
    target_bare = target_jid.split('/')[0] if '/' in target_jid else target_jid
    if len(splitdata) == 2:
        try:
            level = int(splitdata[1])
        except ValueError:
            bot.reply(mtype, source, 'eee?')
            return
        bot.change_access_perm_glob(target_bare, level)
        bot.reply(mtype, source, 'global access granted')
    else:
        bot.change_access_perm_glob(target_bare)
        bot.reply(mtype, source, 'global access withdrawn')

def get_access_levels(bot):
    try:
        with open(bot.globaccess_file, 'r', encoding='utf-8') as f:
            bot.globaccess = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        bot.globaccess = {}
    for admin in bot.admins:
        bot.globaccess[admin] = 100
    bot.save_globaccess()

    try:
        with open(bot.accbyconf_file, 'r', encoding='utf-8') as f:
            bot.accbyconffile = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        bot.accbyconffile = {}
    bot.accbyconf = {}

def setup(bot):
    handler_access_login.bot = bot
    handler_access_logout.bot = bot
    handler_access_view_access.bot = bot
    handler_access_set_access.bot = bot
    handler_access_set_access_glob.bot = bot

    bot.register_command(
        handler_access_login, 'login', access=0,
        desc='Login as bot admin, the command must be type on private!',
        syntax='login <password>', examples=['login secret'],
        category=['access', 'admin', 'all']
    )
    bot.register_command(
        handler_access_logout, 'logout', access=0,
        desc='Logout as bot admin.',
        syntax='logout', examples=['logout'],
        category=['access', 'admin', 'all']
    )
    bot.register_command(
        handler_access_view_access, 'access', access=0,
        desc='Show access level of a user.\n-100 ... (full description)',
        syntax='access [nick]', examples=['access', 'access guy'],
        category=['access', 'admin', 'all']
    )
    bot.register_command(
        handler_access_set_access, 'set_access', access=15,
        desc='Grant or withdrawn local access...',
        syntax='set_access <nick> <level> [permanent]',
        examples=['set_access guy 20', 'set_access guy 30 permanent'],
        category=['access', 'admin', 'all']
    )
    bot.register_command(
        handler_access_set_access_glob, 'globacc', access=100,
        desc='Grant or withdrawn global access...',
        syntax='globacc <nick> <level>',
        examples=['globacc guy 100', 'globacc guy'],
        category=['access', 'superadmin', 'all']
    )

    bot.stage0_init.append(get_access_levels)