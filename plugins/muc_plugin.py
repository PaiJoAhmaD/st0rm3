#===istalismanplugin===
# -*- coding: utf-8 -*-

import asyncio

def handler_ban_everywhere(mtype, source, parameters):
    bot = handler_ban_everywhere.bot
    jid = parameters.strip()
    if not jid:
        bot.reply(mtype, source, 'Specify a JID to ban everywhere')
        return
    reason = 'go to hell'
    for room in list(bot.groupchats.keys()):
        asyncio.ensure_future(
            bot.plugin['xep_0045'].set_affiliation(
                room, jid, affiliation='outcast',
                reason=bot.get_bot_nick(room) + ': ' + reason
            )
        )

def handler_unban_everywhere(mtype, source, parameters):
    bot = handler_unban_everywhere.bot
    jid = parameters.strip()
    if not jid:
        bot.reply(mtype, source, 'Specify a JID to unban everywhere')
        return
    for room in list(bot.groupchats.keys()):
        asyncio.ensure_future(
            bot.plugin['xep_0045'].set_affiliation(
                room, jid, affiliation='none'
            )
        )

def handler_member_everywhere(mtype, source, parameters):
    bot = handler_member_everywhere.bot
    jid = parameters.strip()
    if not jid:
        bot.reply(mtype, source, 'Specify a JID to make member everywhere')
        return
    reason = 'congratulations! Be a good member'
    for room in list(bot.groupchats.keys()):
        asyncio.ensure_future(
            bot.plugin['xep_0045'].set_affiliation(
                room, jid, affiliation='member',
                reason=bot.get_bot_nick(room) + ': ' + reason
            )
        )

def handler_unmember_everywhere(mtype, source, parameters):
    bot = handler_unmember_everywhere.bot
    jid = parameters.strip()
    if not jid:
        bot.reply(mtype, source, 'Specify a JID to unmember everywhere')
        return
    for room in list(bot.groupchats.keys()):
        asyncio.ensure_future(
            bot.plugin['xep_0045'].set_affiliation(
                room, jid, affiliation='none'
            )
        )

def setup(bot):
    handler_ban_everywhere.bot = bot
    handler_unban_everywhere.bot = bot
    handler_member_everywhere.bot = bot
    handler_unmember_everywhere.bot = bot

    bot.register_command(
        handler_member_everywhere, 'fullmember', access=100,
        desc='Member a JID everywhere where bot sits in conference',
        syntax='fullmember <jid>', examples=['fullmember guy@jsmart.web.id'],
        category=['superadmin', 'all']
    )
    bot.register_command(
        handler_unmember_everywhere, 'fullunmember', access=100,
        desc='Unmember a JID everywhere where bot sits in conference',
        syntax='fullunmember <jid>', examples=['fullunmember guy@jsmart.web.id'],
        category=['superadmin', 'all']
    )
    bot.register_command(
        handler_ban_everywhere, 'fullban', access=100,
        desc='Ban a JID everywhere where bot sits in conference',
        syntax='fullban <jid>', examples=['fullban guy@jsmart.web.id'],
        category=['superadmin', 'all']
    )
    bot.register_command(
        handler_unban_everywhere, 'fullunban', access=100,
        desc='Unban a JID everywhere bot sits',
        syntax='fullunban <jid>', examples=['fullunban guy@jsmart.web.id'],
        category=['superadmin', 'all']
    )