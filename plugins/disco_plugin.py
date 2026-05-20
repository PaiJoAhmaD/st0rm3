#===istalismanplugin===
# -*- coding: utf-8 -*-

import logging
import re

async def handler_disco(mtype, source, parameters):
    bot = handler_disco.bot
    if not parameters:
        bot.reply(mtype, source, 'and?')
        return

    parts = parameters.split(maxsplit=2)
    tojid = parts[0]
    stop = None
    srch = None
    node = None

    if len(parts) == 1:
        stop = 10 if mtype == 'public' else 50
    elif len(parts) >= 2:
        try:
            stop = int(parts[1])
            if len(parts) >= 3:
                srch = parts[2]
        except ValueError:
            srch = parts[1]
            stop = 10 if mtype == 'public' else 50

    # Batas aman
    if mtype == 'public':
        stop = min(stop, 50)
    else:
        stop = min(stop, 250)

    # Pisahkan node jika ada '#'
    if '#' in tojid:
        tojid, node = tojid.split('#', 1)

    try:
        # Gunakan xep_0030 untuk mengambil daftar item
        items = await bot.plugin['xep_0030'].get_items(tojid, node=node or '')
    except Exception as e:
        logging.error(f"disco error: {e}")
        bot.reply(mtype, source, 'sorry… can’t reach that JID')
        return

    if not items:
        bot.reply(mtype, source, 'disco empty')
        return

    # Format hasil seperti plugin asli
    disco_data = []
    trig = False
    for item in items:
        name = item.get('name', '')
        jid = item.get('jid', '')
        if name:
            m = re.match(r'^(.*) \((\d+)\)$', name)
            if m:
                disco_data.append([m.group(1), jid, int(m.group(2))])
                trig = True
            else:
                if not trig:
                    disco_data.append([name, jid])
        else:
            disco_data.append([jid])

    sorted_data = sortdis(disco_data)

    # Bangun jawaban
    dis_out = []
    total = 0
    for item in sorted_data:
        if total >= stop:
            break
        if len(item) == 3:
            if srch:
                if srch.endswith('@') and item[1] and item[1].startswith(srch):
                    dis_out.append(f'{total+1}) {item[0]} [{item[1]}]: {item[2]}')
                    break
                elif srch and srch.lower() not in item[0].lower() and (not item[1] or srch.lower() not in item[1].lower()):
                    continue
            total += 1
            dis_out.append(f'{total}) {item[0]} [{item[1]}]: {item[2]}')
        elif len(item) == 2:
            if srch and srch.lower() not in item[0].lower() and (not item[1] or srch.lower() not in item[1].lower()):
                continue
            total += 1
            dis_out.append(f'{total}) {item[0]} [{item[1]}]')
        else:
            if srch and srch.lower() not in item[0].lower():
                continue
            total += 1
            dis_out.append(f'{total}) {item[0]}')

    if dis_out:
        if total < len(disco_data):
            dis_out.append(f'total {len(disco_data)} users')
        rep = 'disco routined:\n' + '\n'.join(dis_out)
    else:
        rep = 'disco empty'

    bot.reply(mtype, source, rep)


def sortdis(dis):
    disd = [x for x in dis if len(x) >= 3 and isinstance(x[2], int)]
    diss = [x for x in dis if x not in disd]
    disd.sort(key=lambda y: -y[2])
    diss.sort(key=lambda y: (y[0].lower() if y else ''))
    return disd + diss


def setup(bot):
    handler_disco.bot = bot
    bot.register_command(
        handler_disco,
        'disco',
        access=10,
        desc='Service Discovery: disco <jid> [count] [search]',
        syntax='disco <server> [count] [search]',
        examples=['disco jabber.aq', 'disco conference.jabber.ru 5 qwerty'],
        category=['muc', 'info', 'all']
    )