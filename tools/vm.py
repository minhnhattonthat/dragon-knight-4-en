"""Linear parser for DK4 script blocks.

parse() returns ops: {'off', 'kind': 'cmd'|'text', 'raw', ...}
  cmd : 'op', optional 'targets' (16-bit block offsets it can jump to)
  text: 'codes' = list of codes; 0x00 = newline, 0x11 = blank cell, glyph codes, dictionary codes (>= 0x6CC)
"""
import sys
from dk4 import ARGS, JUMP_ARG, CHOICE_N, DICT_FIRST, DICT_COUNT, load_rom, load_glyphs, blocks

END_OPS = {0x13, 0x16, 0x3A}  # ops after which a block may end (tail bytes are other data)


class ParseError(Exception):
    def __init__(self, msg, pos):
        super().__init__('%s at %X' % (msg, pos))
        self.pos = pos


def parse(data, glyphs, start=0, end=None):
    end = len(data) if end is None else end
    ops, i = [], start
    text = None
    while i < end:
        b = data[i]
        if b == 0x10:
            text = None
            if i + 1 >= end:
                raise ParseError('truncated cmd', i)
            op = data[i + 1]
            if op not in ARGS:
                raise ParseError('unknown op %02X' % op, i)
            n = ARGS[op]
            targets = []
            if op == 0x0C:  # choice: layout byte, then (CHOICE_N[layout] + 1) 16-bit jump targets (last = cancel)
                if data[i + 2] >= len(CHOICE_N):
                    raise ParseError('bad choice layout', i)
                cnt = CHOICE_N[data[i + 2]] + 1
                targets = [data[i + 3 + 2 * k] | data[i + 4 + 2 * k] << 8 for k in range(cnt)]
                n = 1 + 2 * cnt
            raw = bytes(data[i:i + 2 + n])
            o = {'off': i, 'kind': 'cmd', 'op': op, 'raw': raw}
            if op in JUMP_ARG:
                k = 2 + JUMP_ARG[op]
                targets = [raw[k] | raw[k + 1] << 8]
            if targets:
                o['targets'] = targets
            ops.append(o)
            i += 2 + n
            continue
        if b == 0x00:
            code, n = 0, 1
        elif b < 0x10:
            if i + 1 >= end:
                raise ParseError('truncated code', i)
            code, n = b << 8 | data[i + 1], 2
            if code not in glyphs and not DICT_FIRST <= code < DICT_FIRST + DICT_COUNT:
                raise ParseError('bad code %X' % code, i)
        else:
            code, n = b, 1
            if code != 0x11 and code not in glyphs:
                raise ParseError('bad code %X' % code, i)
        if text is None:
            text = {'off': i, 'kind': 'text', 'raw': b'', 'codes': []}
            ops.append(text)
        text['raw'] += bytes(data[i:i + n])
        text['codes'].append(code)
        i += n
    return ops


def block_start(data):
    """Offset where the script starts: after the header of 16-bit entry pointers (first word), 0 if no header."""
    first = data[0] | data[1] << 8
    return first if data[0] != 0x10 and first < len(data) else 0


def parse_block(rom, glyphs, blk):
    """Parse one table block. Returns (start, end, ops). Blocks whose length word over-covers (the last table
    entries) end at the last END_OPS op before unparsable bytes."""
    idx, scene, off, ln = blk
    # a bogus length word can over-cover the next block (table entries 56-58): stop at any other block's len word
    nxt = min([b[2] for b in blocks(rom) if off < b[2] < off + 2 + ln], default=None)
    if nxt is not None:
        ln = nxt - off - 2
    data = rom[off + 2:off + 2 + ln]
    start = block_start(data)
    try:
        ops = parse(data, glyphs, start)
        return start, len(data), ops
    except ParseError as e:
        ops = parse(data, glyphs, start, e.pos)
        # drop trailing partial text run, cut after the last end op
        while ops and not (ops[-1]['kind'] == 'cmd' and ops[-1]['op'] in END_OPS):
            ops.pop()
        if not ops:
            raise
        last = ops[-1]
        return start, last['off'] + len(last['raw']), ops


def render_codes(codes, glyphs):
    out = []
    for c in codes:
        if c == 0:
            out.append('\n')
        elif c == 0x11:
            out.append('_')
        else:
            out.append(glyphs.get(c, '{D%03X}' % c))
    return ''.join(out)


def main():
    rom = load_rom()
    g = load_glyphs()
    sel = int(sys.argv[1]) if len(sys.argv) > 1 else None
    for blk in blocks(rom):
        idx, scene, off, ln = blk
        if sel is not None and idx != sel:
            continue
        try:
            start, end, ops = parse_block(rom, g, blk)
            nt = sum(1 for o in ops if o['kind'] == 'text')
            print('%02d %06X len=%04X start=%04X end=%04X ops=%d text=%d' % (idx, off, ln, start, end, len(ops), nt))
        except ParseError as e:
            print('%02d %06X len=%04X FAIL %s' % (idx, off, ln, e))
            continue
        if sel is not None:
            for o in ops:
                if o['kind'] == 'text':
                    print('  %04X  "%s"' % (o['off'], render_codes(o['codes'], g).replace('\n', '/')))
                else:
                    print('  %04X  cmd %02X %s%s' % (o['off'], o['op'], o['raw'][2:].hex(' '),
                                                    '  -> ' + ','.join('%04X' % t for t in o['targets'])
                                                    if 'targets' in o else ''))


if __name__ == '__main__':
    main()
