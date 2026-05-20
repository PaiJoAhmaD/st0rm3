#===istalismanplugin===
# -*- coding: utf-8 -*-

#  Talisman plugin
#  more_plugin.py

def handler_more(mtype, source, parameters):
    bot = handler_more.bot
    if mtype != 'private':
        room = source[1]
        cfg = bot.gch_config(room)
        if cfg.get('more', 1) == 1:
            last_msg = bot.last['gch'].get(room, {}).get('msg')
            if last_msg:
                bot.reply(mtype, source, last_msg)
    else:
        bot.reply(mtype, source, 'a sense?')

def handler_more_control(mtype, source, parameters):
    # Admin control untuk fitur more (implementasi nanti)
    pass

def handler_more_outmsg(target, body, obody):
    """Dipanggil setiap kali bot mengirim pesan, menyimpan sisa teks panjang."""
    bot = handler_more_outmsg.bot
    # Hanya untuk room yang diikuti bot
    if target in bot.groupchats:
        cfg = bot.gch_config(target)
        if cfg.get('more', 1) == 1:
            last_msg = bot.last['gch'].get(target, {}).get('msg')
            if hash(obody) != last_msg:
                if len(obody) > 1000:
                    # Simpan karakter ke-1001 dst.
                    bot.last['gch'][target]['msg'] = obody[1000:]

def init_more(gch):
    """Inisialisasi per room, memastikan konfigurasi 'more' ada."""
    bot = init_more.bot
    cfg = bot.gch_config(gch)
    if 'more' not in cfg:
        cfg['more'] = 1
        bot.save_gch_config(gch, cfg)
    if cfg.get('more', 1):
        if gch not in bot.last['gch']:
            bot.last['gch'][gch] = {}
        bot.last['gch'][gch]['msg'] = ''

def setup(bot):
    handler_more.bot = bot
    handler_more_control.bot = bot
    handler_more_outmsg.bot = bot
    init_more.bot = bot

    bot.register_command(
        handler_more, 'more', access=0,
        desc='Show the rest of a truncated long message.',
        syntax='more', examples=['more'],
        category=['muc', 'all']
    )
    bot.register_command(
        handler_more_control, 'more*', access=20,
        desc='Admin control for more feature.',
        syntax='more*', examples=['more*'],
        category=['admin', 'muc', 'all']
    )

    # Daftarkan outgoing message handler
    bot.outgoing_message_handlers.append(handler_more_outmsg)

    # Daftarkan stage1 init
    bot.stage1_init.append(init_more)