#===istalismanplugin===
# -*- coding: utf-8 -*-

import asyncio
import logging
import random

from slixmpp import Iq
from slixmpp.xmlstream import register_stanza_plugin
from slixmpp.plugins.xep_0199 import Ping

# Konstanta dari bot asli
ROLES = {'none': 0, 'visitor': 0, 'participant': 10, 'moderator': 15}
AFFILIATIONS = {'none': 0, 'member': 1, 'admin': 5, 'owner': 15}

# ID ping yang sedang menunggu balasan
check_pending = []

# =============================================================================
# Handler presence: update akses lokal berdasarkan role/affiliation
# =============================================================================
async def handler_presence_ra_change(presence):
    bot = handler_presence_ra_change.bot
    fromjid = presence['from']
    room = fromjid.bare
    nick = fromjid.resource

    if room not in bot.groupchats:
        return
    if nick not in bot.groupchats.get(room, {}):
        return

    # Dapatkan JID sebenarnya
    try:
        jid = presence['muc']['jid']
    except KeyError:
        jid = None
    if not jid:
        # Fallback: gunakan full JID (mungkin tidak akurat)
        jid_full = str(fromjid)
        jid = jid_full.split('/')[0] if '/' in jid_full else jid_full

    if not jid:
        return

    # Jika sudah ada akses global atau permanen lokal, abaikan
    if jid in bot.globaccess:
        return
    if room in bot.accbyconffile and jid in bot.accbyconffile[room]:
        return

    # Ambil role & affiliation dari stanza MUC
    role = presence['muc']['role']
    aff = presence['muc']['affiliation']

    accr = ROLES.get(role, 0)
    acca = AFFILIATIONS.get(aff, 0)
    access = accr + acca

    # Tandai moderator
    if role == 'moderator' or bot.user_level(jid, room) >= 15:
        bot.groupchats[room][nick]['ismoder'] = 1
    else:
        bot.groupchats[room][nick]['ismoder'] = 0

    bot.change_access_temp(room, jid, access)

# =============================================================================
# Handler presence: kick jika nick adalah command/macro
# =============================================================================
async def handler_presence_nickcommand(presence):
    bot = handler_presence_nickcommand.bot
    fromjid = presence['from']
    room = fromjid.bare
    nick = fromjid.resource

    if room not in bot.groupchats:
        return

    # Cek apakah kode status 303 (perubahan nick)
    status_codes = presence['muc'].get('status_codes', [])
    if '303' in status_codes:
        # Nick baru setelah perubahan
        new_nick = presence['muc'].get('nick')
        if new_nick:
            nick = new_nick
    else:
        # Nick saat ini
        pass

    nicksource = nick.strip().lower()

    # Periksa apakah nick termasuk command atau macro
    is_command = nicksource in bot.commands
    is_gmacro = hasattr(bot, 'gmacrolist') and nicksource in bot.gmacrolist
    is_lmacro = False
    if room in getattr(bot, 'macrolist', {}):
        is_lmacro = nicksource in bot.macrolist[room]

    if is_command or is_gmacro or is_lmacro:
        reason = bot.get_bot_nick(room) + ': your nickname is invalid here'
        try:
            await bot.plugin['xep_0045'].set_role(room, nick, 'none', reason=reason)
        except Exception as e:
            logging.error(f"Gagal kick {nick} di {room}: {e}")

# =============================================================================
# Keep‑alive: ping setiap room secara periodik
# =============================================================================
async def iqkeepalive_and_s2scheck():
    bot = iqkeepalive_and_s2scheck.bot
    while True:
        await asyncio.sleep(300)  # 5 menit
        for room in list(bot.groupchats.keys()):
            nick = bot.get_bot_nick(room)
            if not nick:
                continue
            # Buat IQ ping
            iq = bot.make_iq_get()
            iq_id = 'p' + str(random.randrange(1, 1000))
            check_pending.append(iq_id)
            iq['id'] = iq_id
            iq['to'] = f'{room}/{nick}'
            # Tambahkan elemen <ping xmlns='urn:xmpp:ping' />
            iq.append(Ping())

            try:
                resp = await iq.send()
                # Balasan diterima
                if resp:
                    error = resp['error']
                    if error and error['code'] in ('405',):
                        pass  # tidak di-support, biarkan
                    # Kalau sukses, tidak apa
            except Exception as e:
                # Timeout atau error lain -> reconnect room
                logging.warning(f"Ping gagal ke {room}/{nick}: {e}")
                # Jadwalkan join ulang setelah 60 detik
                await asyncio.sleep(60)
                bot.join_room(room, nick)

            # Hapus ID dari daftar pending
            if iq_id in check_pending:
                check_pending.remove(iq_id)

# =============================================================================
# Setup plugin
# =============================================================================
def setup(bot):
    handler_presence_ra_change.bot = bot
    handler_presence_nickcommand.bot = bot
    iqkeepalive_and_s2scheck.bot = bot

    # Daftarkan handler presence
    bot.add_event_handler('presence', handler_presence_ra_change)
    bot.add_event_handler('presence', handler_presence_nickcommand)

    # Daftarkan keep‑alive sebagai task background
    bot.stage2_init.append(lambda b: asyncio.ensure_future(iqkeepalive_and_s2scheck()))