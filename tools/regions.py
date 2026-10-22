"""Split script text runs into regions (the unit replaced in place by a far call).

A region is a text run (glyph codes, 00 newlines, 11 blanks, dictionary refs), cut at every jump target.
Each region gets a stable id '<blockoff>_<off>' (block = ROM offset of its len word, off = offset in the body).
Shared blocks (table entries pointing at the same ROM block) are listed once.
"""
from dk4 import load_rom, load_glyphs, blocks, dict_entries
from vm import parse_block, parse

# VM text streams outside the block table: (pseudo block index, rom start, rom end, cpu bank).
# The VM runs them in place (base = ROM address), so jump targets are CPU addresses in that bank.
# 60 = ending epilogue (module $A2=$15, 81:D5AB -> 86:8000; entry table 86:821B, 4 bytes: cond, portrait, ptr16)
# 61-67 = battle event text in bank $85 (victory, rescues, taunts, stat-ups). Direct loaders `LDA #$85 / STA $02 /
# LDY #ptr / STY $00 / JSR $D81D` (84:826F ...) and 32-entry pointer tables (one word per party member, read by
# 84:DEDE and friends) at 85:D0FB, D44C, DB40, E245, E985, F106; each span runs from the end of a table to the next.
EXTRA_STREAMS = [(60, 0x3028C, 0x320C7, 0x86),
                 (61, 0x2C45B, 0x2D0FB, 0x85), (62, 0x2D13B, 0x2D44C, 0x85), (63, 0x2D48C, 0x2DB40, 0x85),
                 (64, 0x2DB80, 0x2E245, 0x85), (65, 0x2E285, 0x2E985, 0x85), (66, 0x2E9C5, 0x2F106, 0x85),
                 (67, 0x2F146, 0x2FFA3, 0x85)]


def stream_ops(rom, glyphs, blk):
    """(start, end, ops) with offsets relative to the body start (blk[2] + 2) and targets as body offsets."""
    if blk[0] < 60:
        return parse_block(rom, glyphs, blk)
    idx, bank, start, end = blk[0], blk[1], blk[2] + 2, blk[2] + 2 + blk[3]
    ops = parse(rom, glyphs, start, end)
    out = []
    for o in ops:
        o = dict(o)
        o['off'] -= start
        if 'targets' in o:
            o['targets'] = [(((bank & 0x7F) << 15) | (t & 0x7FFF)) - start for t in o['targets']]
        out.append(o)
    return 0, end - start, out


def unique_blocks(rom):
    seen, out = set(), []
    for b in blocks(rom):
        if b[2] in seen:
            continue
        seen.add(b[2])
        out.append(b)
    for idx, start, end, bank in EXTRA_STREAMS:   # pseudo block: (idx, bank, 'len word' offset, length)
        out.append((idx, bank, start - 2, end - start))
    return out


def code_len(c):
    return 2 if c >= 0x100 else 1


def regions(rom=None, glyphs=None):
    """Yield dicts: id, block (table idx), boff (block rom off), off (body offset), raw, codes, next_op, prev_op."""
    rom = rom or load_rom()
    glyphs = glyphs or load_glyphs()
    for blk in unique_blocks(rom):
        start, end, ops = stream_ops(rom, glyphs, blk)
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
