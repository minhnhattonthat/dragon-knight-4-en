"""Show the ops before a parse failure: vmfail.py BLOCKIDX [n_ops]"""
import sys
from dk4 import load_rom, load_glyphs, blocks
from vm import parse, ParseError, render_codes

rom = load_rom()
g = load_glyphs()
bi = int(sys.argv[1])
n = int(sys.argv[2]) if len(sys.argv) > 2 else 12
idx, scene, off, ln = blocks(rom)[bi]
data = rom[off + 2:off + 2 + ln]
first = data[0] | data[1] << 8
start = first if data[0] != 0x10 and first < ln else 0
pos = start
ops = []
try:
    parse(data, g, start)
    print('ok')
except ParseError as e:
    print(e)
    bad = int(str(e).split(' at ')[1], 16)
    # reparse up to bad
    ops = parse(data, g, start, bad) if bad > start else []
for o in ops[-n:]:
    if o['kind'] == 'text':
        print('  %04X  "%s"  [%s]' % (o['off'], render_codes(o['codes'], g).replace('\n', '/'), o['raw'].hex(' ')))
    elif o['kind'] == 'cmd':
        print('  %04X  cmd %02X %s' % (o['off'], o['op'], o['raw'][2:].hex(' ')))
    else:
        print('  %04X  NL' % o['off'])
if ops:
    b = int(str(e).split(' at ')[1], 16)
    print('  bytes at fail: ' + data[b - 8:b + 24].hex(' '))
