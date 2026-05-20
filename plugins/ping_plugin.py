#===istalismanplugin===
# -*- coding: utf-8 -*-

import asyncio
import time
import logging

async def handler_ping(mtype, source, parameters):
    bot = handler_ping.bot
    room = source[1]
    requester = source[2]

    target_jid = None
    target_name = None

    if parameters:
        param = parameters.strip()
        # Cek apakah itu nick di room yang sama
        if room in bot.groupchats and param in bot.groupchats[room] and bot.groupchats[room][param].get('ishere'):
            target_jid = bot.groupchats[room][param]['jid']
            target_name = param
        else:
            # Anggap sebagai JID langsung
            target_jid = param
            target_name = param
    else:
        # Targetkan pengirim
        target_jid = source[0]          # full JID (room/nick)
        target_name = 'you'

    if not target_jid:
        bot.reply(mtype, source, 'where is the guy? :-O')
        return

    t0 = time.time()
    try:
        # Gunakan xep_0092 (Software Version) untuk mengirim IQ dan menunggu balasan
        result = await bot.plugin['xep_0092'].get_version(target_jid)
        t1 = time.time()
        rtt = round(t1 - t0, 3)
        rep = f'pong from {target_name} {rtt} seconds'
    except Exception as e:
        logging.warning(f'Ping to {target_jid} failed: {e}')
        rep = 'not ping'

    bot.reply(mtype, source, rep)


def setup(bot):
    handler_ping.bot = bot

    # Pastikan plugin xep_0092 tersedia
    if 'xep_0092' not in bot.plugin:
        bot.register_plugin('xep_0092')

    bot.register_command(
        handler_ping,
        'ping',
        access=0,
        desc='Ping you, a certain nick, or a server/JID.',
        syntax='ping [nick|server]',
        examples=['ping', 'ping guy', 'ping jsmart.web.id'],
        category=['info', 'muc', 'all']
    )