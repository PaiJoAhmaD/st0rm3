#===istalismanplugin===
# -*- coding: utf-8 -*-

import time

def handler_help_help(mtype, source, parameters):
    bot = handler_help_help.bot
    ctglist = []

    if parameters and parameters.strip() in bot.commands:
        cmd_info = bot.commands[parameters.strip()]
        rep = cmd_info['desc'] + '\nCategories: '
        categories = cmd_info.get('category', [])
        rep += ', '.join(categories)
        rep += '\nUse: ' + cmd_info.get('syntax', '')
        rep += '\nExample:'
        for example in cmd_info.get('examples', []):
            rep += '\n  >>  ' + example
        rep += '\nNecessary level of access: ' + str(cmd_info.get('access', 0))

        room = source[1]
        if room in bot.comm_off and parameters.strip() in bot.comm_off[room]:
            rep += '\nThis command has been power-off in this conference!!!'
    else:
        rep = (
            'write a word "commands" (without quotation marks), to get the list of commands, '
            '"help of <commands>" for the receipt of help on a command, '
            'macrolist for the receipt of list of macros, '
            'and also macroacc <macro> for the receipt of level of access to the certain macro\n'
            'p.s. look the level of access in private'
        )

    bot.reply(mtype, source, rep)

def handler_help_commands(mtype, source, parameters):
    bot = handler_help_commands.bot
    date = time.strftime('%a, %d %b %Y', time.gmtime())
    groupchat = source[1]

    if parameters:
        rep = []
        dsbl = []
        total = 0
        catcom = set()
        for cmd, info in bot.commands.items():
            if parameters in info.get('category', []):
                catcom.add(cmd)
        if not catcom:
            bot.reply(mtype, source, 'does it exist? :-O')
            return

        for cat in catcom:
            if bot.has_access(source, bot.commands[cat]['access'], groupchat):
                if groupchat in bot.comm_off and cat in bot.comm_off[groupchat]:
                    dsbl.append(cat)
                else:
                    rep.append(cat)
                    total += 1

        if rep:
            if mtype == 'public':
                bot.reply(mtype, source, 'sent to private')
            rep.sort()
            answer = (
                f'List of commands is in a category <{parameters}> on {date}:\n\n'
                + ', '.join(rep)
                + f' - ({total} items)'
            )
            if dsbl:
                dsbl.sort()
                answer += '\n\nThe followings commands has been power-offs in this conference:\n\n' + ', '.join(dsbl)
            bot.reply('private', source, answer)
        else:
            bot.reply(mtype, source, 'dream ]:->')
    else:
        cats = set()
        for info in bot.commands.values():
            cats.update(info.get('category', []))
        cats = ', '.join(sorted(cats))
        if mtype == 'public':
            bot.reply(mtype, source, 'sent to private')
        reply_text = (
            f'List of commands is in a category on {date}\n'
            + cats
            + '\n\nTo view the list of commands contained in a category, type "commands category" '
              'without quotation marks, for example "commands all"'
        )
        bot.reply('private', source, reply_text)

def setup(bot):
    handler_help_help.bot = bot
    handler_help_commands.bot = bot

    bot.register_command(
        handler_help_help, 'help', access=0,
        desc='Show detail information about a certain command.',
        syntax='help [command]', examples=['help', 'help ping'],
        category=['help', 'info', 'all']
    )
    bot.register_command(
        handler_help_commands, 'commands', access=0,
        desc='Shows the list of all of categories of commands.',
        syntax='commands [category]', examples=['commands', 'commands all'],
        category=['help', 'info', 'all']
    )

    if not hasattr(bot, 'comm_off'):
        bot.comm_off = {}