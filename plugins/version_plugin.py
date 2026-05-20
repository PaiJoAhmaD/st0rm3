#===istalismanplugin===
# -*- coding: utf-8 -*-

import asyncio
import logging

def handler_version(mtype, source, parameters):
    bot = handler_version.bot
    room = source[1]

    if parameters:
        param = parameters.strip()
        # Jika nick pernah terlihat di room (ada di GROUPCHATS), gunakan MUC
        if room in bot.groupchats and param in bot.groupchats[room]:
            target_jid = room + '/' + param
        else:
            target_jid = param
    else:
        target_jid = source[0]   # full JID pengirim (room/nick)

    # Jadwalkan query di event loop utama
    loop = bot.loop or asyncio.get_event_loop()
    asyncio.run_coroutine_threadsafe(
        query_version(bot, mtype, source, target_jid), loop
    )

async def query_version(bot, mtype, source, jid):
    """Kirim IQ version dan balas hasilnya."""
    try:
        result = await bot.plugin['xep_0092'].get_version(jid)
        if result:
            sv = result['software_version']
            name = sv['name'] or '[no name]'
            version = sv['version'] or '[no ver]'
            os = sv['os'] or '[no os]'
            rep = f'\nClient    :  {name}\n' \
                  f'Version :  {version}\n' \
                  f'Os       :  {os}'
        else:
            rep = 'there is not such thing'
    except Exception as e:
        logging.warning(f'Version query to {jid} failed: {e}')
        rep = 'he |-)'

    bot.reply(mtype, source, rep)

def setup(bot):
    handler_version.bot = bot

    if 'xep_0092' not in bot.plugin:
        bot.register_plugin('xep_0092')

    bot.register_command(
        handler_version,
        'version',
        access=0,
        desc='Shows software version of a client or server.',
        syntax='version [nick|server]',
        examples=['version', 'version guy', 'version jsmart.web.id'],
        category=['info', 'muc', 'all']
    )