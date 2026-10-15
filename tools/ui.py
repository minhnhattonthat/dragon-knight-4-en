"""UI strings drawn cell by cell (menus, notebooks, status, battle pools) -> precomposed English cells.

Each JP code in these strings is one 16x14 cell. English is rendered with the VWF font into cells
(hires screens: font as in dialogue; lores screens: one px per font unit) and each distinct cell gets a code
$0B00-$0DFF (asm: b160_hook/b1b0_hook/vwf_hook draw them from $E1:8000).

ui/ui.json entries:
  {"id", "kind": "linear"|"pool", "off": "0xNNNN", "mode": "hires"|"lores", "en": "Field | Field", ...}
  linear: 00-terminated string; fields = runs of glyphs separated by blank cells; English field k starts at
          the JP field's cell and may use cells up to (next field start - 1).
          "refs": [hex offsets of `LDY #imm16` operands to patch if the string must move] + "bank_refs".
  pool:   fixed byte range [off, end) inside a pointer-table pool; English must use exactly the JP cell count
          (rendered left-aligned, padded with blank cells); bytes must fit (2 per English cell).
"""
import json
import os
from dk4 import ROOT, load_glyphs
import font_en

PRE_FIRST, PRE_END = 0xB00, 0xE00
BLANK = 0x11


def jp_cells(rom, off, end=None):
    """List of codes (one per cell) from off until 00 (or end). Returns (codes, byte_length incl. terminator)."""
    out, i = [], off
    while (end is None and rom[i] != 0) or (end is not None and i < end):
        b = rom[i]
        if b < 0x10:
            out.append(b << 8 | rom[i + 1])
            i += 2
        else:
            out.append(b)
            i += 1
    return out, i - off + (1 if end is None else 0)


def render(text, mode):
    """Bitmap rows (list of 14 ints, arbitrary width) and width in px."""
    rows, x = [0] * 14, 0
    unit = 2 if mode == 'hires' else 1
    gap = font_en.GAP if mode == 'hires' else 1
    cols = []
    for ch in text:
        body, desc = font_en.G[ch]
        w = len(body[0])
        for cx in range(w):
            col = 0
            for r, line in enumerate(body + (desc or [])):
                if line[cx] == '#':
                    col |= 1 << (2 + r)
            cols.extend([col] * unit)
        cols.extend([0] * gap)
    while cols and cols[-1] == 0:
        cols.pop()
    return cols


def cells_from_cols(cols, n):
    """Split column bitmaps into n cells of 16 px -> list of 14-row tuples (bit 15 = leftmost)."""
    cells = []
    for c in range(n):
        rows = [0] * 14
        for x in range(16):
            px = c * 16 + x
            if px < len(cols):
                for r in range(14):
                    if cols[px] >> r & 1:
                        rows[r] |= 0x8000 >> x
        cells.append(tuple(rows))
    return cells


def cell_bytes(rows):
    """Game font format (28 bytes): see font.py."""
    b = bytearray(28)
    for r in range(14):
        lo, hi = rows[r] >> 8 & 0xFF, rows[r] & 0xFF
        if r < 8:
            b[r], b[8 + r] = lo, hi
        else:
            b[16 + r - 8], b[22 + r - 8] = lo, hi
    return bytes(b)


class Pre:
    def __init__(self):
        self.codes = {}

    def code(self, rows):
        if not any(rows):
            return BLANK
        if rows not in self.codes:
            c = PRE_FIRST + len(self.codes)
            if c >= PRE_END:
                raise SystemExit('out of precomposed UI codes')
            self.codes[rows] = c
        return self.codes[rows]

    def write(self, img, off):
        for rows, c in self.codes.items():
            o = off + (c - PRE_FIRST) * 28
            img[o:o + 28] = cell_bytes(rows)


def fields_of(codes, split=2):
    """[(start_cell, ncells)] runs of non-blank cells separated by >= split blanks."""
    fields, i, n = [], 0, len(codes)
    while i < n:
        if codes[i] == BLANK:
            i += 1
            continue
        s = i
        while i < n and not (codes[i] == BLANK and (split == 1 or i + 1 >= n or codes[i + 1] == BLANK)):
            i += 1
        fields.append((s, i - s))
    return fields


def encode_cells(cell_codes):
    out = bytearray()
    for c in cell_codes:
        out += bytes([c]) if c < 0x100 else bytes([c >> 8, c & 0xFF])
    return bytes(out)


def build_linear(e, rom, pre):
    off = int(e['off'], 16)
    codes, nbytes = jp_cells(rom, off)
    fs = fields_of(codes, e.get('split', 2))
    if e.get('cells'):  # the window is wider than the JP string: extra blank cells allowed at the end
        codes = codes + [BLANK] * (e['cells'] - len(codes))
    en = [s.strip() for s in e['en'].split(' | ')]
    if len(en) != len(fs):
        raise ValueError('%s: %d fields needed, got %d' % (e['id'], len(fs), len(en)))
    out = [BLANK] * len(codes)
    for k, ((start, n), text) in enumerate(zip(fs, en)):
        limit = (fs[k + 1][0] - 1 if k + 1 < len(fs) else len(codes)) - start
        limit = min(limit, e.get('max_cells', limit))
        cols = render(text, e['mode'])
        need = (len(cols) + 15) // 16
        if need > limit:
            raise ValueError('%s: %r needs %d cells, %d free' % (e['id'], text, need, limit))
        for i, rows in enumerate(cells_from_cols(cols, need)):
            out[start + i] = pre.code(rows)
    return off, nbytes, encode_cells(out) + b'\x00'


def build_pool(e, rom, pre):
    off, end = int(e['off'], 16), int(e['end'], 16)
    codes, _ = jp_cells(rom, off, end)
    n = len(codes)
    cols = render(e['en'], e['mode'])
    need = (len(cols) + 15) // 16
    if need > n:
        raise ValueError('%s: %r needs %d cells, pool slot has %d' % (e['id'], e['en'], need, n))
    cells = [pre.code(r) for r in cells_from_cols(cols, n)]
    data = encode_cells(cells)
    if len(data) > end - off:
        raise ValueError('%s: %d bytes, slot has %d' % (e['id'], len(data), end - off))
    return off, end - off, data + bytes([BLANK]) * (end - off - len(data))


def load():
    return json.load(open(os.path.join(ROOT, 'ui', 'ui.json'), encoding='utf-8'))


RELOC_OFF, RELOC_END = 0x30E000, 0x310000   # $E1:E000-$E1:FFFF: relocated UI strings


def apply(img, rom, pre_off):
    """Write every UI string with English into img. Returns list of errors."""
    pre, errs = Pre(), []
    reloc = RELOC_OFF
    for e in load():
        if not e.get('en'):
            continue
        try:
            if e['kind'] == 'linear':
                off, nbytes, data = build_linear(e, rom, pre)
                if len(data) <= nbytes:
                    img[off:off + nbytes] = data + b'\x00' * (nbytes - len(data))
                else:
                    # relocate: patch every `LDA #bank / STA $02 / LDY #ptr / STY $00` site listed in refs
                    if not e.get('refs'):
                        raise ValueError('%s: %d bytes > %d and no refs to relocate' % (e['id'], len(data), nbytes))
                    if reloc + len(data) > RELOC_END:
                        raise ValueError('UI relocation area full')
                    img[reloc:reloc + len(data)] = data
                    cpu = ((reloc >> 15) + 0x80) << 16 | 0x8000 | (reloc & 0x7FFF)
                    for r in e['refs']:
                        r = int(r, 16)
                        assert img[r] == 0xA9 and img[r + 2] == 0x85 and img[r + 4] == 0xA0, (e['id'], hex(r))
                        img[r + 1] = cpu >> 16
                        img[r + 5:r + 7] = (cpu & 0xFFFF).to_bytes(2, 'little')
                    img[off:off + nbytes] = bytes([BLANK]) * (nbytes - 1) + b'\x00'
                    reloc += len(data)
            else:
                off, nbytes, data = build_pool(e, rom, pre)
                img[off:off + nbytes] = data
        except ValueError as ex:
            errs.append(str(ex))
    pre.write(img, pre_off)
    return errs


def dump(rom):
    """Print JP of every ui.json entry (for filling in English)."""
    g = load_glyphs()
    for e in load():
        if e['kind'] == 'linear':
            codes, n = jp_cells(rom, int(e['off'], 16))
        else:
            codes, n = jp_cells(rom, int(e['off'], 16), int(e['end'], 16))
        print(e['id'], n, ''.join('_' if c == BLANK else g.get(c, '[%X]' % c) for c in codes))


if __name__ == '__main__':
    from dk4 import load_rom
    dump(load_rom())
