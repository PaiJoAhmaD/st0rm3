#===istalismanplugin===
# -*- coding: utf-8 -*-

"""
Plugin Manager untuk storm-py3
Command:
  plugins                      -> tampilkan daftar plugin yang dimuat
  plugins reload <nama>        -> muat ulang plugin tertentu
  plugins load <nama>          -> muat plugin baru (dari folder plugins/)
  plugins unload <nama>        -> nonaktifkan plugin (hapus command & handler)
"""

import importlib
import logging

def handler_plugins(mtype, source, parameters):
    bot = handler_plugins.bot
    args = parameters.strip().split() if parameters.strip() else []

    if not args:
        # Tampilkan daftar plugin yang sedang aktif
        if bot.plugins:
            plist = '\n'.join(f'  • {name}' for name in sorted(bot.plugins.keys()))
            reply = f'Active plugins:\n{plist}'
        else:
            reply = 'No plugins loaded.'
        bot.reply(mtype, source, reply)
        return

    action = args[0].lower()
    if len(args) < 2 and action != 'list':
        bot.reply(mtype, source, 'Usage: plugins [list|reload <name>|load <name>|unload <name>]')
        return

    plugin_name = args[1] if len(args) > 1 else None

    if action == 'list':
        if bot.plugins:
            plist = '\n'.join(f'  • {name}' for name in sorted(bot.plugins.keys()))
            reply = f'Active plugins:\n{plist}'
        else:
            reply = 'No plugins loaded.'
        bot.reply(mtype, source, reply)
        return

    if not plugin_name:
        bot.reply(mtype, source, 'Specify plugin name.')
        return

    if action == 'reload':
        if plugin_name not in bot.plugins:
            bot.reply(mtype, source, f'Plugin "{plugin_name}" not found.')
            return
        # Hentikan dulu, lalu impor ulang
        try:
            # Unload existing
            _unload_plugin(bot, plugin_name)
            # Load lagi
            mod = importlib.import_module(f'plugins.{plugin_name}')
            importlib.reload(mod)   # pastikan ambil versi terbaru
            if hasattr(mod, 'setup'):
                mod.setup(bot)
            bot.plugins[plugin_name] = mod
            logging.info(f'Plugin "{plugin_name}" reloaded.')
            bot.reply(mtype, source, f'Plugin "{plugin_name}" reloaded successfully.')
        except Exception as e:
            logging.error(f'Failed to reload plugin "{plugin_name}": {e}')
            bot.reply(mtype, source, f'Error reloading "{plugin_name}": {str(e)}')

    elif action == 'load':
        if plugin_name in bot.plugins:
            bot.reply(mtype, source, f'Plugin "{plugin_name}" is already loaded.')
            return
        try:
            mod = importlib.import_module(f'plugins.{plugin_name}')
            if hasattr(mod, 'setup'):
                mod.setup(bot)
            bot.plugins[plugin_name] = mod
            logging.info(f'Plugin "{plugin_name}" loaded.')
            bot.reply(mtype, source, f'Plugin "{plugin_name}" loaded successfully.')
        except Exception as e:
            logging.error(f'Failed to load plugin "{plugin_name}": {e}')
            bot.reply(mtype, source, f'Error loading "{plugin_name}": {str(e)}')

    elif action == 'unload':
        if plugin_name not in bot.plugins:
            bot.reply(mtype, source, f'Plugin "{plugin_name}" not loaded.')
            return
        try:
            _unload_plugin(bot, plugin_name)
            del bot.plugins[plugin_name]
            logging.info(f'Plugin "{plugin_name}" unloaded.')
            bot.reply(mtype, source, f'Plugin "{plugin_name}" unloaded.')
        except Exception as e:
            logging.error(f'Failed to unload plugin "{plugin_name}": {e}')
            bot.reply(mtype, source, f'Error unloading "{plugin_name}": {str(e)}')

    else:
        bot.reply(mtype, source, f'Unknown action: {action}')

def _unload_plugin(bot, plugin_name):
    """
    Menghapus semua command & handler yang didaftarkan oleh plugin.
    Plugin harus menyimpan daftar command yang didaftarkan,
    atau kita bisa iterasi semua command dan hapus yang handler-nya dari modul.
    """
    mod = bot.plugins.get(plugin_name)
    if not mod:
        return
    # Hapus command yang handler-nya ada di modul ini
    to_remove = []
    for cmd, handler in bot.command_handlers.items():
        if handler.__module__ == mod.__name__:
            to_remove.append(cmd)
    for cmd in to_remove:
        del bot.command_handlers[cmd]
        if cmd in bot.commands:
            del bot.commands[cmd]
    # Hapus dari registri lain (opsional: message handler, dll) jika ada

def setup(bot):
    handler_plugins.bot = bot

    # Simpan referensi ke dict plugins di bot (jika belum ada)
    if not hasattr(bot, 'plugins'):
        bot.plugins = {}   # name -> module

    # Isi bot.plugins dengan modul yang sudah dimuat (dari load_plugins awal)
    # Ini agar daftar sinkron
    if hasattr(bot, 'plugin_list'):
        for mod in bot.plugin_list:
            name = mod.__name__.split('.')[-1]
            bot.plugins[name] = mod

    bot.register_command(
        handler_plugins,
        'plugins',
        access=40,
        desc='Manage plugins: list, reload, load, unload.',
        syntax='plugins [list|reload <name>|load <name>|unload <name>]',
        examples=[
            'plugins',
            'plugins reload admin_plugin',
            'plugins load new_plugin',
            'plugins unload ping_plugin'
        ],
        category=['admin', 'all']
    )