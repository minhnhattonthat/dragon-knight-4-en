"""Split script text runs into regions (the unit replaced in place by a far call).

A region is a text run (glyph codes, 00 newlines, 11 blanks, dictionary refs), cut at every jump target.
Each region gets a stable id '<blockoff>_<off>' (block = ROM offset of its len word, off = offset in the body).
Shared blocks (table entries pointing at the same ROM block) are listed once.
"""
from dk4 import load_rom, load_glyphs, blocks, dict_entries
from vm import parse_block


def unique_blocks(rom):
    seen, out = set(), []
    for b in blocks(rom):
        if b[2] in seen:
            continue
        seen.add(b[2])
        out.append(b)
    return out


def code_len(c):
    return 2 if c >= 0x100 else 1


def regions(rom=None, glyphs=None):
    """Yield dicts: id, block (table idx), boff (block rom off), off (body offset), raw, codes, next_op, prev_op."""
    rom = rom or load_rom()
    glyphs = glyphs or load_glyphs()
    for blk in unique_blocks(rom):
        start, end, ops = parse_block(rom, glyphs, blk)
        targets = set()
        for o in ops:
            targets.update(o.get('targets', []))
        for k, o in enumerate(ops):
            if o['kind'] != 'text':
                continue
            prev_op = ops[k - 1] if k > 0 else None
            next_op = ops[k + 1] if k + 1 < len(ops) else None
            # cut points inside the run
            pieces, cur, pos = [], [], o['off']
            cur_off = pos
            for c in o['codes']:
                if pos in targets and cur:
                    pieces.append((cur_off, cur))
                    cur, cur_off = [], pos
                cur.append(c)
                pos += code_len(c)
            pieces.append((cur_off, cur))
            for n, (off, codes) in enumerate(pieces):
                ln = sum(code_len(c) for c in codes)
                yield {
                    'id': '%06X_%04X' % (blk[2], off), 'block': blk[0], 'boff': blk[2], 'off': off,
                    'len': ln, 'codes': codes,
                    'prev_op': prev_op['op'] if (n == 0 and prev_op and prev_op['kind'] == 'cmd') else None,
                    'next_op': next_op['op'] if (n == len(pieces) - 1 and next_op and next_op['kind'] == 'cmd') else None,
                    'next_raw': next_op['raw'] if (n == len(pieces) - 1 and next_op) else None,
                    'target': off in targets,
                }


if __name__ == '__main__':
    import collections
    rs = list(regions())
    print('regions', len(rs))
    print('len dist', sorted(collections.Counter(min(r['len'], 6) for r in rs).items()))
    print('next ops', collections.Counter(r['next_op'] for r in rs).most_common(20))
    print('prev ops', collections.Counter(r['prev_op'] for r in rs).most_common(20))
    # positioning blanks: 11 not directly after a newline / region start
    pos_blank = 0
    for r in rs:
        prev = 0
        for c in r['codes']:
            if c == 0x11 and prev not in (0, None, 0x11) and prev != 'start':
                pos_blank += 1
                break
            prev = c
    print('regions with mid-line blanks', pos_blank)
