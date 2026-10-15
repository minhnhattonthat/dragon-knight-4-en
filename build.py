"""Dragon Knight 4 English build.

python -X utf8 build.py build     -> build/dk4_en.sfc   (translated units; untranslated regions stay Japanese)
python -X utf8 build.py marker    -> build/dk4_marker.sfc (every region replaced by '[id] marker text')
python -X utf8 build.py identity  -> build/dk4_identity.sfc (no engine, no text: must equal the original)
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from dk4 import load_rom, load_glyphs  # noqa: E402
from regions import regions, unique_blocks  # noqa: E402
from segments import units, tokens, lines_of, choice_fields, is_choice  # noqa: E402
import layout  # noqa: E402
import font_en  # noqa: E402
import ui  # noqa: E402
import gfx_buttons  # noqa: E402
import gfx_popups  # noqa: E402

ASAR = os.path.join(ROOT, 'tools', 'asar', 'asar.exe')
SIZE = 0x400000
FARSHORT_OFF = 0x300000          # $E0:8000
FONT_OFF = 0x304000              # $E0:C000
FONTW_OFF = 0x304C00             # $E0:CC00
PRE_OFF, PRE_FIRST, PRE_END = 0x308000, 0xB00, 0xE00   # $E1:8000: precomposed English UI cells
TEXT_START, TEXT_END = 0x318000, 0x400000   # banks $E3-$FF ($E2 = UI copy of bank $84, see tools/ui.py)
SHORT_FIRST, SHORT_LAST = 0x833, 0xAFF
PAGE_RESET_OPS = {0x01, 0x13, 0x15, 0x16, 0x0C, 0x3A}
PANGRAM = 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs. '


def file_to_cpu(off):
    return ((off >> 15) + 0x80) << 16 | 0x8000 | (off & 0x7FFF)


def load_names():
    m = {}
    for ln in open(os.path.join(ROOT, 'tbl', 'names_en.tsv'), encoding='utf-8'):
        if ln.strip():
            jp, en = ln.rstrip('\n').split('\t')
            m[jp] = en
    return m


def load_script():
    d = {}
    sd = os.path.join(ROOT, 'script')
    for fn in sorted(os.listdir(sd)):
        if fn.endswith('.json'):
            for e in json.load(open(os.path.join(sd, fn), encoding='utf-8')):
                d[e['id']] = e
    return d


def english_of(e, script):
    if e.get('en'):
        return e['en']
    if e.get('dup') and script[e['dup']].get('en'):
        return script[e['dup']]['en']
    return None


class Alloc:
    def __init__(self, img):
        self.img, self.pos = img, TEXT_START

    def put(self, data):
        if (self.pos & 0x7FFF) + len(data) > 0x8000:
            self.pos = (self.pos | 0x7FFF) + 1
        if self.pos + len(data) > TEXT_END:
            raise SystemExit('out of text space')
        p = self.pos
        self.img[p:p + len(data)] = data
        self.pos += len(data)
        return p


def write_font(img):
    for i in range(96):
        ch = chr(0x20 + i)
        rows, w = font_en.glyph(ch) if ch in font_en.G else ([0] * 14, 0)
        for r in range(14):
            img[FONT_OFF + i * 28 + 2 * r] = rows[r] & 0xFF
            img[FONT_OFF + i * 28 + 2 * r + 1] = rows[r] >> 8
        img[FONTW_OFF + i] = w


def region_seg_info(r, rom, g):
    """[(speaker_jp, portrait)] per unit, in order (mirrors segments.units)."""
    toks = tokens(r['codes'], rom, g)
    info, cur = [], None
    for t in toks:
        if t[0] == 'name':
            cur = (t[2], t[3])
            info.append(cur)
        elif cur is None:
            cur = ('', None)
            info.append(cur)
    return info, toks


def choice_layout(toks):
    """Per line: [(start_cell, cells_available or None)] from the JP fields."""
    lay = []
    for line in lines_of(toks):
        fs = choice_fields(line)
        row = []
        for k, (start, jp) in enumerate(fs):
            nxt = fs[k + 1][0] if k + 1 < len(fs) else layout.CELLS
            row.append((start, nxt - start - (1 if k + 1 < len(fs) else 0)))
        lay.append(row)
    return lay


def marker_text(uid, n):
    if os.environ.get('DK4_STRESS') == uid[:2]:  # width gate on one block: 3 full lines per unit
        return '[%s] %s' % (uid, (PANGRAM * 3)[:125].rsplit(' ', 1)[0])
    return '[%s] %s' % (uid, PANGRAM[:20 * max(1, n)].rsplit(' ', 1)[0])


MIDLINE_LEAD = 8   # cells kept free on the first line of a mid-line region (an inserted name is up to 8 cells)


def midline_targets(rom, g):
    """{(block file offset, body offset)} of jump targets reached from a jump that follows text with no newline,
    e.g. "<leader name>" JUMP -> "、 / I want you to...": the English continues on a line that already holds a name."""
    from vm import parse_block
    out = set()
    for blk in unique_blocks(rom):
        try:
            _, _, ops = parse_block(rom, g, blk)
        except Exception:   # pseudo blocks (epilogue stream) have no jump-into-midline cases
            continue
        for prev, o in zip(ops, ops[1:]):
            if o.get('targets') and prev['kind'] == 'text' and prev['raw'][-1:] != b'\x00':
                out.update((blk[2], t) for t in o['targets'])
    return out


def build(mode):
    rom = load_rom()
    g = load_glyphs()
    img = bytearray(rom) + b'\xff' * (SIZE - len(rom))
    if mode == 'identity':
        return bytes(rom)
    write_font(img)
    names = load_names()
    script = load_script()
    alloc = Alloc(img)
    short_next = SHORT_FIRST
    stats = {'regions': 0, 'english': 0, 'japanese': 0, 'errors': 0}
    errors = []
    prev_end = {}
    shared = {}
    midline = midline_targets(rom, g)
    for r in regions(rom, g):
        stats['regions'] += 1
        us = units(r, rom, g)
        ids = ['%s.%d' % (r['id'], u['sid']) for u in us]
        if all(u['form'] == 'empty' for u in us) and not any(t for t in us if t['speaker']):
            continue
        # English text per unit
        texts = []
        for uid, u in zip(ids, us):
            if u['form'] == 'empty':
                texts.append('')
            elif mode == 'marker':
                short = uid.split('_', 1)[1]
                if u['form'] == 'choice':
                    texts.append(' / '.join(' | '.join('c%d' % k for k, _ in enumerate(l.split(' | ')))
                                            for l in u['jp'].split(' / ')))
                else:
                    texts.append(marker_text('%02d:%s' % (r['block'], short), u['nlines']))
            else:
                texts.append(english_of(script[uid], script) if uid in script else None)
        if any(t is None for t in texts):
            stats['japanese'] += 1
            continue
        try:
            if us[0]['form'] == 'choice':
                toks = tokens(r['codes'], rom, g)
                lay = choice_layout(toks)
                en_lines = [[f.strip() for f in l.split(' | ')] for l in texts[0].split(' / ')]
                if len(en_lines) != sum(1 for x in lay if x):
                    raise layout.LayoutError('choice needs %d lines' % sum(1 for x in lay if x))
                it = iter(en_lines)
                fields = [next(it) if x else [] for x in lay]
                if any(len(a) != len(b) for a, b in zip(fields, lay)):
                    raise layout.LayoutError('choice needs %s fields per line' % [len(x) for x in lay if x])
                body = layout.choice_region(fields, lay)
                end_line = 0
            else:
                info, toks = region_seg_info(r, rom, g)
                segs = []
                for (sp, portrait), t in zip(info, texts):
                    segs.append((names.get(sp, sp) if sp else '', portrait, t))
                start_line = 0
                key = (r['boff'], r['off'])
                if r['prev_op'] is None and r['off'] in prev_end.get(r['boff'], {}):
                    start_line = prev_end[r['boff']][r['off']]
                trailing = bool(toks) and toks[-1][0] == 'nl'
                first = layout.CELLS - MIDLINE_LEAD if (r['boff'], r['off']) in midline else layout.CELLS
                body, end_line = layout.dlg_region(segs, start_line, trailing, first)
        except layout.LayoutError as ex:
            stats['errors'] += 1
            errors.append('%s: %s' % (r['id'], ex))
            continue
        if r['next_op'] is None or r['next_op'] not in PAGE_RESET_OPS:
            prev_end.setdefault(r['boff'], {})[r['off'] + r['len']] = end_line
        if r['len'] < 2:
            stats['japanese'] += 1
            continue
        far = body + layout.END
        if far not in shared:
            shared[far] = file_to_cpu(alloc.put(far))
        cpu = shared[far]
        if r['len'] >= 6:   # 0F ptr24 skip16
            tok = bytes([0x0F, cpu & 0xFF, cpu >> 8 & 0xFF, cpu >> 16]) + (r['len'] - 4).to_bytes(2, 'little')
        else:               # short code -> FARSHORT entry: ptr24, skip8
            if short_next > SHORT_LAST:
                raise SystemExit('out of short codes')
            k = short_next - SHORT_FIRST
            img[FARSHORT_OFF + 4 * k:FARSHORT_OFF + 4 * k + 4] = cpu.to_bytes(3, 'little') + bytes([r['len'] - 2])
            tok = bytes([short_next >> 8, short_next & 0xFF])
            short_next += 1
        at = r['boff'] + 2 + r['off']
        img[at:at + r['len']] = tok + b'\x11' * (r['len'] - len(tok))
        stats['english'] += 1
    # assemble the engine last (it patches code only)
    if mode == 'build':
        img[gfx_buttons.OFF:gfx_buttons.OFF + gfx_buttons.NT * 32] = gfx_buttons.patch(rom)
        for off, data in gfx_popups.patch(rom).items():
            img[off:off + len(data)] = data
        ui_errs = ui.apply(img, rom, PRE_OFF)
        errors += ['UI ' + x for x in ui_errs]
    return bytes(img), stats, errors


def assemble(path):
    r = subprocess.run([ASAR, '--fix-checksum=off', os.path.join(ROOT, 'asm', 'dk4.asm'), path],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('asar failed:\n' + r.stdout + r.stderr)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'build'
    os.makedirs(os.path.join(ROOT, 'build'), exist_ok=True)
    out = os.path.join(ROOT, 'build', {'build': 'dk4_en.sfc', 'marker': 'dk4_marker.sfc',
                                       'identity': 'dk4_identity.sfc'}[mode])
    res = build(mode)
    if mode == 'identity':
        open(out, 'wb').write(res)
        print('identity ->', out)
        return
    img, stats, errors = res
    open(out, 'wb').write(img)
    assemble(out)
    for e in errors[:40]:
        print('LAYOUT', e)
    print(mode, '->', out, stats)
    sys.exit(1 if errors and mode == 'build' else 0)


if __name__ == '__main__':
    main()
