#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import json
import logging
import os
import sys
import time
import inspect
import threading
import importlib
import platform
from pathlib import Path

from slixmpp import ClientXMPP, Iq
from slixmpp.plugins.xep_0199 import Ping
from slixmpp.xmlstream import register_stanza_plugin

# Daftarkan stanza Ping untuk semua Iq (digunakan presence_plugin)
register_stanza_plugin(Iq, Ping)

# =============================================================================
# Config Loader (path relatif ke lokasi script)
# =============================================================================
def load_config(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file not found: {path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)

try:
    CFG = load_config()
except Exception as e:
    logging.error(f"Failed to load config: {e}")
    sys.exit(1)

CONNECT_SERVER = CFG["CONNECT_SERVER"]
PORT = CFG["PORT"]
JID = CFG["JID"]
PASSWORD = CFG["PASSWORD"]
RESOURCE = CFG["RESOURCE"]
DEFAULT_NICK = CFG["DEFAULT_NICK"]
ADMINS = CFG["ADMINS"]
ADMIN_PASSWORD = CFG.get("ADMIN_PASSWORD", "")
AUTO_RESTART = CFG.get("AUTO_RESTART", False)

GROUPCHAT_CACHE_FILE = "dynamic/chatrooms.list"
GLOBACCESS_FILE = "dynamic/globaccess.cfg"
ACCBYCONF_FILE = "dynamic/accbyconf.cfg"
PLUGIN_DIR = "plugins"

# =============================================================================
# Global registries
# =============================================================================
COMMANDS = {}
COMMAND_HANDLERS = {}
MESSAGE_HANDLERS = []
OUTGOING_MESSAGE_HANDLERS = []
JOIN_HANDLERS = []
LEAVE_HANDLERS = []
IQ_HANDLERS = []
PRESENCE_HANDLERS = []
STAGE0_INIT = []
STAGE1_INIT = []
STAGE2_INIT = []

GROUPCHATS = {}
LAST = {"c": "", "t": 0, "gch": {}}
INFO = {"start": 0, "msg": 0, "prs": 0, "iq": 0, "cmd": 0, "thr": 0}
COMMOFF = {}
GLOBACCESS = {}
ACCBYCONF = {}
ACCBYCONFFILE = {}
smph = threading.BoundedSemaphore(value=30)

# =============================================================================
# Bot Class
# =============================================================================
class StormBot(ClientXMPP):
    def __init__(self, jid, password):
        super().__init__(jid, password)
        self.register_plugin('xep_0045')

        # Plugin untuk merespons query version (XEP-0092)
        self.register_plugin('xep_0092')
        self['xep_0092'].software_name = 'stOrm'
        self['xep_0092'].version = '1.02-19 (Python 3)'
        self['xep_0092'].os = f"{platform.system()} {platform.release()} / Python {sys.version_info.major}.{sys.version_info.minor}"

        self.admins = ADMINS
        self.admin_password = ADMIN_PASSWORD
        self.default_nick = DEFAULT_NICK
        self.commands = COMMANDS
        self.command_handlers = COMMAND_HANDLERS
        self.groupchats = GROUPCHATS
        self.last = LAST
        self.info = INFO
        self.stage0_init = STAGE0_INIT
        self.stage1_init = STAGE1_INIT
        self.stage2_init = STAGE2_INIT
        self.comm_off = COMMOFF
        self.globaccess = GLOBACCESS
        self.accbyconf = ACCBYCONF
        self.accbyconffile = ACCBYCONFFILE
        self.globaccess_file = GLOBACCESS_FILE
        self.accbyconf_file = ACCBYCONF_FILE
        self.macrolist = {}
        self.gmacrolist = {}

        self.message_handlers = MESSAGE_HANDLERS
        self.outgoing_message_handlers = OUTGOING_MESSAGE_HANDLERS
        self.join_handlers = JOIN_HANDLERS
        self.leave_handlers = LEAVE_HANDLERS
        self.iq_handlers = IQ_HANDLERS
        self.presence_handlers = PRESENCE_HANDLERS

        self.add_event_handler("session_start", self.on_session_start)
        self.add_event_handler("message", self.on_message)
        self.add_event_handler("groupchat_message", self.on_groupchat_message)
        self.add_event_handler("disconnected", self.on_disconnected)

    # =========================================================================
    # Core event handlers
    # =========================================================================
    async def on_session_start(self, event):
        self.send_presence()
        await self.get_roster()

        for init_func in self.stage0_init:
            try:
                init_func(self)
            except Exception as e:
                logging.error(f"Stage0 init error: {e}")

        await self.join_rooms_from_cache()

        # Jalankan stage2 init (background task seperti ping keepalive)
        for init_func in self.stage2_init:
            try:
                init_func(self)
            except Exception as e:
                logging.error(f"Stage2 init error: {e}")

        logging.info("Bot siap!")

    async def join_rooms_from_cache(self):
        if not os.path.exists(GROUPCHAT_CACHE_FILE):
            return
        try:
            with open(GROUPCHAT_CACHE_FILE, "r", encoding="utf-8") as f:
                rooms = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Could not load chatrooms cache: {e}")
            return

        for room, cfg in rooms.items():
            nick = cfg.get("nick", self.default_nick)
            passw = cfg.get("passw")
            for init_func in self.stage1_init:
                try:
                    init_func(room)
                except Exception as e:
                    logging.error(f"Stage1 init error for {room}: {e}")

            try:
                await self.plugin['xep_0045'].join_muc(room, nick, password=passw)
                logging.info(f"Joined {room}")
                self.add_event_handler(f"muc::{room}::got_online", self.make_muc_online_handler(room))
                self.add_event_handler(f"muc::{room}::got_offline", self.make_muc_offline_handler(room))
            except Exception as e:
                logging.error(f"Gagal join {room}: {e}")

    def make_muc_online_handler(self, room):
        async def handler(presence):
            nick = presence['muc']['nick']
            jid = presence['muc']['jid']
            if room not in self.groupchats:
                self.groupchats[room] = {}
            self.groupchats[room][nick] = {
                'jid': jid,
                'idle': time.time(),
                'joined': time.time(),
                'ishere': 1,
                'status': '',
                'stmsg': ''
            }
            for h in self.join_handlers:
                threading.Thread(target=h, args=(room, nick, presence['muc']['affiliation'], presence['muc']['role'])).start()
        return handler

    def make_muc_offline_handler(self, room):
        async def handler(presence):
            nick = presence['muc']['nick']
            reason = presence['muc']['reason'] or ""
            code = presence['muc']['status_code']
            if room in self.groupchats and nick in self.groupchats[room]:
                del self.groupchats[room][nick]
            for h in self.leave_handlers:
                threading.Thread(target=h, args=(room, nick, reason, code)).start()
        return handler

    async def on_message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await self.process_message(msg, 'private')

    async def on_groupchat_message(self, msg):
        await self.process_message(msg, 'public')

    async def process_message(self, msg, mtype):
        body = msg['body'].strip() if msg['body'] else ""
        if not body:
            return

        fromjid = msg['from']
        room = fromjid.bare
        nick = fromjid.resource

        if room in self.groupchats and nick in self.groupchats[room]:
            self.groupchats[room][nick]['idle'] = time.time()

        for handler in self.message_handlers:
            with smph:
                threading.Thread(target=handler, args=(mtype, [str(fromjid), room, nick], body)).start()

        parts = body.split()
        if parts:
            cmd = parts[0].lower()
            if cmd in self.command_handlers:
                args = " ".join(parts[1:]) if len(parts) > 1 else ""
                source = [str(fromjid), room, nick]
                if not self.has_access(source, self.commands[cmd]['access'], room):
                    self.reply(mtype, source, "insufficient privileges")
                    return

                # Jalankan command dengan benar (async atau sync)
                handler = self.command_handlers[cmd]
                if asyncio.iscoroutinefunction(handler):
                    asyncio.run_coroutine_threadsafe(
                        handler(mtype, source, args),
                        self.loop
                    )
                else:
                    threading.Thread(
                        target=handler,
                        args=(mtype, source, args)
                    ).start()

                self.info['cmd'] += 1
                self.last['t'] = time.time()
                self.last['c'] = cmd

    def on_disconnected(self, event):
        logging.warning("DISCONNECTED")
        # Tidak perlu loop.stop(), biarkan event loop menangani

    # =========================================================================
    # Plugin helpers
    # =========================================================================
    def register_command(self, handler, name, access=0, **kwargs):
        name = name.lower()
        handler.bot = self
        self.command_handlers[name] = handler
        self.commands[name] = {
            'access': access,
            'handler': handler.__name__,
            'desc': kwargs.get('desc', ''),
            'syntax': kwargs.get('syntax', ''),
            'examples': kwargs.get('examples', []),
            'category': kwargs.get('category', [])
        }

    def send_msg(self, target, body, mtype="groupchat"):
        obody = body
        if len(body) > 1000:
            body = body[:1000] + ' >>>>'

        if mtype == "groupchat":
            self.send_message(mto=target, mbody=body, mtype="groupchat")
        else:
            self.send_message(mto=target, mbody=body, mtype="chat")

        for handler in self.outgoing_message_handlers:
            try:
                handler(target, body, obody)
            except Exception as e:
                logging.error(f"Outgoing handler error: {e}")

    def reply(self, ltype, source, body):
        if ltype == "public":
            room = source[1]
            nick = source[2]
            self.send_msg(room, f"{nick}: {body}")
        else:
            self.send_msg(source[0], body, mtype="chat")

    def get_true_jid(self, source):
        if isinstance(source, list):
            full = source[0]
        else:
            full = source
        if not isinstance(full, str):
            full = str(full)
        return full.split('/')[0] if '/' in full else full

    def get_bot_nick(self, room):
        if os.path.exists(GROUPCHAT_CACHE_FILE):
            try:
                with open(GROUPCHAT_CACHE_FILE, 'r', encoding='utf-8') as f:
                    rooms = json.load(f)
                if room in rooms and rooms[room].get('nick'):
                    return rooms[room]['nick']
            except (FileNotFoundError, json.JSONDecodeError) as e:
                logging.warning(f"Could not read bot nick from cache: {e}")
        return self.default_nick

    def user_level(self, jid, room=None):
        if isinstance(jid, list):
            jid = self.get_true_jid(jid)
        bare = jid.split('/')[0] if '/' in jid else jid
        if bare in self.globaccess:
            return self.globaccess[bare]
        if room:
            if room in self.accbyconffile and bare in self.accbyconffile[room]:
                return self.accbyconffile[room][bare]
            if room in self.accbyconf and bare in self.accbyconf[room]:
                return self.accbyconf[room][bare]
        return 0

    def has_access(self, source, level, room):
        jid = self.get_true_jid(source)
        return self.user_level(jid, room) >= level

    def change_access_temp(self, room, jid, level):
        if room not in self.accbyconf:
            self.accbyconf[room] = {}
        self.accbyconf[room][jid] = level

    def change_access_perm(self, room, jid, level=None):
        if room not in self.accbyconffile:
            self.accbyconffile[room] = {}
        if level is not None:
            self.accbyconffile[room][jid] = level
        else:
            self.accbyconffile[room].pop(jid, None)
        if room in self.accbyconf:
            if level is not None:
                self.accbyconf[room][jid] = level
            else:
                self.accbyconf[room].pop(jid, None)
        self.save_accbyconf()

    def change_access_perm_glob(self, jid, level=None):
        if level is not None:
            self.globaccess[jid] = level
        else:
            self.globaccess.pop(jid, None)
        self.save_globaccess()

    def save_globaccess(self):
        with open(self.globaccess_file, 'w', encoding='utf-8') as f:
            json.dump(self.globaccess, f)

    def save_accbyconf(self):
        with open(self.accbyconf_file, 'w', encoding='utf-8') as f:
            json.dump(self.accbyconffile, f)

    def gch_config(self, room):
        path = f'dynamic/{room}/config.cfg'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        if not os.path.exists(path):
            with open(path, 'w', encoding='utf-8') as f:
                json.dump({"popups": 1, "autoaway": 0, "status": {"status": "", "show": ""}}, f)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logging.warning(f"Error reading room config: {e}")
            return {"popups": 1, "autoaway": 0, "status": {"status": "", "show": ""}}

    def save_gch_config(self, room, cfg):
        path = f'dynamic/{room}/config.cfg'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f)

    def join_room(self, room, nick=None, password=None):
        if nick is None:
            nick = self.default_nick
        asyncio.ensure_future(
            self.plugin['xep_0045'].join_muc(room, nick, password=password)
        )

    def leave_room(self, room, reason=''):
        asyncio.ensure_future(
            self.plugin['xep_0045'].leave_muc(room, self.default_nick, reason)
        )

    def load_plugins(self):
        plugin_path = Path(PLUGIN_DIR)
        if not plugin_path.exists():
            logging.info(f"Plugin directory not found: {PLUGIN_DIR}")
            return
        for file in plugin_path.iterdir():
            if file.suffix == ".py" and file.name != "__init__.py":
                name = file.stem
                try:
                    mod = importlib.import_module(f"{PLUGIN_DIR}.{name}")
                    if hasattr(mod, "setup"):
                        mod.setup(self)
                        logging.info(f"Plugin loaded: {name}")
                except Exception as e:
                    logging.error(f"Failed to load {name}: {e}")


# =============================================================================
# Fungsi async untuk menjalankan bot (menunggu disconnect)
# =============================================================================
async def run_bot(bot):
    # connect() di slixmpp modern adalah sync, tidak perlu await
    try:
        bot.connect((CONNECT_SERVER, PORT))
    except Exception as e:
        logging.error(f"Connection failed: {e}")
        return False

    # Tunggu sampai sesi benar-benar dimulai
    session_started = asyncio.Event()
    bot.add_event_handler("session_start", lambda e: session_started.set())
    try:
        await asyncio.wait_for(session_started.wait(), timeout=30)  # 30 detik timeout
    except asyncio.TimeoutError:
        logging.error("Session start timeout")
        bot.disconnect()
        return False

    # Tunggu sampai disconnect
    disconnect_event = asyncio.Event()
    bot.add_event_handler("disconnected", lambda e: disconnect_event.set())
    await disconnect_event.wait()
    return True


# =============================================================================
# Main
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    logging.info("Starting stOrm3 bot...")

    retry_count = 0
    max_retries = 5

    while True:
        try:
            bot = StormBot(JID, PASSWORD)
            bot.load_plugins()
            logging.info(f"Connecting to {CONNECT_SERVER}:{PORT} as {JID}")
            
            success = asyncio.run(run_bot(bot))
            
            if success:
                retry_count = 0
            else:
                retry_count += 1
                
        except KeyboardInterrupt:
            logging.info("Interrupted by user, exiting.")
            break
        except Exception as e:
            logging.exception(f"Bot crashed: {e}")
            retry_count += 1

        if not AUTO_RESTART:
            break

        if retry_count >= max_retries:
            logging.error(f"Max retries ({max_retries}) reached, exiting.")
            break

        logging.info(f"Restarting bot in 5 seconds... (attempt {retry_count})")
        time.sleep(5)

    logging.info("Bot shutdown complete.")
