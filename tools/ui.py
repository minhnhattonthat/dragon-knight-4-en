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
    unit = 2 if mode == 'hires' else 1       # 'thin': one hi-res px per font unit (condensed UI labels)
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


def squeeze(cols):
    """Drop up to 3 blank columns (letter gaps, from the right) so the width fits the cell below."""
    over = len(cols) % 16
    if not 0 < over <= 3:
        return cols
    cols = list(cols)
    i = len(cols) - 2
    while over and i > 0:
        if cols[i] == 0 and cols[i - 1] != 0 and cols[i + 1] != 0:
            del cols[i]
            over -= 1
        i -= 1
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


def lorom_off(cpu):
    return ((cpu & 0x7F0000) >> 1) | (cpu & 0x7FFF)


def to_cpu(off):
    return ((off >> 15) + 0x80) << 16 | 0x8000 | (off & 0x7FFF)


def english_cells(text, ncells, mode, pre, eid):
    """Codes for `text` padded with BLANK to ncells (BLANK cells cost 1 byte)."""
    cols = render(text, mode) if text else []
    need = (len(cols) + 15) // 16
    if need > ncells:
        raise ValueError('%s: %r needs %d cells, has %d' % (eid, text, need, ncells))
    return [pre.code(r) for r in cells_from_cols(cols, need)] + [BLANK] * (ncells - need)


# Bank $84 string tables (unit types, terrain, battle panel, digits, names) are read with $02 = #$84 set at
# these sites; the build copies bank $84 to $E2 and points them there, so strings can grow (E2:F000-FFFF).
BANK84_COPY = 0x310000           # file offset of $E2:8000
BANK84_SITES = [0xF47C, 0x21302, 0x22CF7, 0x25A93]   # `LDA #$84 / STA $02` (file offsets)
E2_ALLOC = [0x317000]            # $E2:F000.. next free byte


def bank84_copy(img, rom):
    img[BANK84_COPY:BANK84_COPY + 0x8000] = rom[0x20000:0x28000]
    for s in BANK84_SITES:
        assert img[s] == 0xA9 and img[s + 1] == 0x84 and img[s + 2] == 0x85 and img[s + 3] == 0x02, hex(s)
        img[s + 1] = 0xE2


def build_table(e, rom, img, pre):
    """String table: count+1 consecutive 16-bit pointers at `table` (CPU address in bank $84; last = end of
    last string). Each entry keeps its JP cell count (blank-padded); new strings go to $E2:F000+ and the
    pointer table in the $E2 copy is rewritten."""
    tab = int(e['table'], 16)
    bank = tab & 0xFF0000
    assert bank == 0x840000
    if e.get('en_tsv'):   # index<TAB>jp<TAB>en rows; missing indices keep the JP string
        rows = {}
        for ln in open(os.path.join(ROOT, 'ui', e['en_tsv']), encoding='utf-8'):
            if ln.strip():
                i, _, en = ln.rstrip('\n').split('\t')
                rows[int(i)] = en
        e = dict(e, en=[rows.get(k) for k in range(e['count'])])
    n = len(e['en'])
    ptrs = [rom[lorom_off(tab) + 2 * k] | rom[lorom_off(tab) + 2 * k + 1] << 8 for k in range(n + 1)]
    tab_off = BANK84_COPY + (lorom_off(tab) - 0x20000)
    for k, text in enumerate(e['en']):
        codes, _ = jp_cells(rom, lorom_off(bank | ptrs[k]), lorom_off(bank | ptrs[k + 1]))
        cells = codes if text is None else english_cells(text, len(codes), e['mode'], pre, '%s[%d]' % (e['id'], k))
        data = encode_cells(cells)
        p = E2_ALLOC[0]
        if p + len(data) > BANK84_COPY + 0x8000:
            raise ValueError('bank $E2 string area full')
        img[p:p + len(data)] = data
        E2_ALLOC[0] += len(data)
        img[tab_off + 2 * k:tab_off + 2 * k + 2] = (0x8000 | (p & 0x7FFF)).to_bytes(2, 'little')
        if k == n - 1:   # end pointer of the last entry
            img[tab_off + 2 * n:tab_off + 2 * n + 2] = (0x8000 | (E2_ALLOC[0] & 0x7FFF)).to_bytes(2, 'little')
    return
    span_lo, span_hi = lorom_off(bank | ptrs[0]), lorom_off(bank | ptrs[n])
    data, newp = bytearray(), []
    for k, text in enumerate(e['en']):
        codes, _ = jp_cells(rom, lorom_off(bank | ptrs[k]), lorom_off(bank | ptrs[k + 1]))
        if text is None:   # keep the JP string (symbols, digits)
            cells = codes
        else:
            cells = english_cells(text, len(codes), e['mode'], pre, '%s[%d]' % (e['id'], k))
        newp.append(ptrs[0] + len(data))
        data += encode_cells(cells)
    newp.append(ptrs[0] + len(data))
    if len(data) > span_hi - span_lo:
        raise ValueError('%s: %d bytes > span %d' % (e['id'], len(data), span_hi - span_lo))
    img[span_lo:span_lo + len(data)] = data
    for k, p in enumerate(newp):
        img[lorom_off(tab) + 2 * k:lorom_off(tab) + 2 * k + 2] = p.to_bytes(2, 'little')


def build_dict_names(e, rom, img, pre):
    """Dictionary entries (85:8ED0 table) rendered as precomposed cells, padded to the JP cell count.
    The new strings go to the relocation area; the dictionary pointer table gets their addresses only if
    they stay in bank $85, so entries are rewritten in place when they fit (2 bytes per cell)."""
    from dk4 import dict_entries, DICT_TABLE, DICT_FIRST
    ents = {c: (a, raw) for c, a, raw in dict_entries(rom)}
    # free space: the dialogue-only fragments (codes in e['free']), unused once the script is English
    lo, hi = (int(x, 16) for x in e['free'])
    pos, end = ents[lo][0], ents[hi][0]
    for code_hex, text in e['en'].items():
        code = int(code_hex, 16)
        a, raw = ents[code]
        codes, _ = jp_cells(rom, a, a + len(raw) - 1)
        cells = english_cells(text, len(codes), e['mode'], pre, '%s %s' % (e['id'], code_hex))
        data = encode_cells(cells) + b'\x00'
        if pos + len(data) > end:
            raise ValueError('%s: dictionary free space exhausted' % e['id'])
        img[pos:pos + len(data)] = data
        cpu = to_cpu(pos)
        assert cpu >> 16 == 0x85
        t = DICT_TABLE + 2 * (code - DICT_FIRST)
        img[t:t + 2] = (cpu & 0xFFFF).to_bytes(2, 'little')
        pos += len(data)


def build_screen(e, rom, img, pre, reloc):
    """A label pool (linear string drawn into consecutive cells; cell k = tiles 4k+4..4k+7) plus an LZ tilemap
    (32x32 words, hi-res: a cell is one column, rows r and r+1 = tiles t and t+2) that places pool cells.
    e: pool_ref (site of LDA #bank/STA $02/LDY #ptr), map (cpu addr), map_bank_ref, map_ptr_ref,
       cells: [["jp", code] | ["blank"] | ["en", text, ncells]], place: [[row, col, cell_index, ncells]],
       clear: [[row, col_from, col_to]] (pool tiles there are blanked first)."""
    import lz
    codes, idx = [], []
    for c in e['cells']:
        idx.append(len(codes))
        if c[0] == 'jp':
            codes.append(int(c[1], 16))
        elif c[0] == 'blank':
            codes.append(BLANK)
        else:
            codes += english_cells(c[1], c[2], e['mode'], pre, '%s %r' % (e['id'], c[1]))
    if len(codes) * 4 + 4 > e.get('max_tile', 0xA0):
        raise ValueError('%s: pool too big (%d cells)' % (e['id'], len(codes)))
    if e.get('exact_cells') and len(codes) != e['exact_cells']:
        raise ValueError('%s: pool must stay %d cells (got %d)' % (e['id'], e['exact_cells'], len(codes)))
    data = encode_cells(codes) + b'\x00'
    p = reloc[0]
    img[p:p + len(data)] = data
    reloc[0] += len(data)
    cpu = to_cpu(p)
    r = int(e['pool_ref'], 16)
    assert img[r] == 0xA9 and img[r + 2] == 0x85 and img[r + 4] == 0xA0, (e['id'], hex(r))
    img[r + 1] = cpu >> 16
    img[r + 5:r + 7] = (cpu & 0xFFFF).to_bytes(2, 'little')
    if not e.get('map'):
        return
    # tilemap
    mcpu = int(e['map'], 16)
    raw, _ = lz.decompress(rom, lorom_off(mcpu))
    m = bytearray(raw)

    def put(row, col, word):
        o = (row * 32 + col) * 2
        m[o:o + 2] = word.to_bytes(2, 'little')

    def get(row, col):
        o = (row * 32 + col) * 2
        return m[o] | m[o + 1] << 8
    attr = e.get('attr', 0x2000)
    for row, c0, c1 in e['clear']:
        for col in range(c0, c1 + 1):
            for rr in (row, row + 1):
                t = get(rr, col) & 0x3FF
                if 0 < t < e.get('max_tile', 0xA0):
                    put(rr, col, attr)
    for row, col, ci, n in e['place']:
        k0 = idx[ci]
        for j in range(n):
            t = 4 * (k0 + j + 1)
            put(row, col + j, attr | t)
            put(row + 1, col + j, attr | (t + 2))
    comp = lz.compress(bytes(m))
    p = reloc[0]
    img[p:p + len(comp)] = comp
    reloc[0] += len(comp)
    cpu = to_cpu(p)
    img[int(e['map_bank_ref'], 16)] = cpu >> 16
    pr = int(e['map_ptr_ref'], 16)
    img[pr:pr + 2] = (cpu & 0xFFFF).to_bytes(2, 'little')


def build_namelist(e, rom, img, pre, reloc):
    """Party-name list: pool string (pool_ref site) + table of 8-cell entries (top 8 words, bottom 8 words,
    LE, at `table` file offset, `count` entries). Each English name gets its own pool cells (thin, squeezed)."""
    names, codes, first = e['names'], [], {}
    for n in names:
        if n in first:
            continue
        cols = squeeze(render(n, e['mode']))
        k = (len(cols) + 15) // 16
        if k > 8:
            raise ValueError('%s: %r too wide' % (e['id'], n))
        first[n] = (len(codes), k)
        codes += [pre.code(r) for r in cells_from_cols(cols, k)]
    if len(codes) * 4 + 4 > e.get('max_tile', 0x100):
        raise ValueError('%s: pool too big (%d cells)' % (e['id'], len(codes)))
    # the upload buffer holds 64 cells (asm: 81:F0E5 patched from 56)
    if len(codes) > 64:
        raise ValueError('%s: %d cells > 64 (upload buffer)' % (e['id'], len(codes)))
    data = encode_cells(codes) + b'\x00'
    p = reloc[0]
    img[p:p + len(data)] = data
    reloc[0] += len(data)
    cpu = to_cpu(p)
    for rh in e.get('pool_refs', [e.get('pool_ref')]):
        r = int(rh, 16)
        assert img[r] == 0xA9 and img[r + 2] == 0x85 and img[r + 4] in (0xA0, 0xA2), (e['id'], hex(r))
        img[r + 1] = cpu >> 16
        img[r + 5:r + 7] = (cpu & 0xFFFF).to_bytes(2, 'little')
    tab = int(e['table'], 16)
    for i, n in enumerate(names):
        k0, k = first[n]
        b = tab + 32 * i
        for j in range(8):
            if j < k:
                t = 4 * (k0 + j + 1)
                img[b + 2 * j:b + 2 * j + 2] = t.to_bytes(2, 'little')
                img[b + 16 + 2 * j:b + 18 + 2 * j] = (t + 2).to_bytes(2, 'little')
            else:
                img[b + 2 * j:b + 2 * j + 2] = b'\x00\x00'
                img[b + 16 + 2 * j:b + 18 + 2 * j] = b'\x02\x00'


def build_strset(e, rom, img, pre, reloc):
    """Strings drawn cell by cell by one routine (00-terminated, codes as in the script), relocated to the UI
    area. e: strings: [[addr, english]], ptr_refs: {addr: [file offsets of LDY #imm16 operands]},
    bank_refs: [file offsets of LDA #bank operands to set to the new bank], tables: [[long_ref, [addrs..]]]
    (long_ref = file offset of a `LDA $bbhhll,x` operand; the table is rebuilt with the new pointers).
    Leading/trailing blank cells of each JP string are kept."""
    new = {}
    bank = None
    for addr_hex, text in e['strings']:
        a = int(addr_hex, 16)
        codes, _ = jp_cells(rom, lorom_off(a))
        lead = len(codes) - len([c for c in codes]) if False else 0
        while lead < len(codes) and codes[lead] == BLANK:
            lead += 1
        trail = 0
        while trail < len(codes) - lead and codes[len(codes) - 1 - trail] == BLANK:
            trail += 1
        cols = render(text, e['mode'])
        if e.get('squeeze'):
            cols = squeeze(cols)
        k = (len(cols) + 15) // 16
        if e.get('max_cells') and k > e['max_cells']:
            raise ValueError('%s: %r needs %d cells > %d' % (e['id'], text, k, e['max_cells']))
        cells = [BLANK] * lead + [pre.code(r) for r in cells_from_cols(cols, k)] + [BLANK] * trail
        data = encode_cells(cells) + b'\x00'
        p = reloc[0]
        img[p:p + len(data)] = data
        reloc[0] += len(data)
        new[a] = to_cpu(p)
        bank = new[a] >> 16
    for a_hex, refs in e.get('ptr_refs', {}).items():
        for r in refs:
            r = int(r, 16)
            assert img[r - 1] == 0xA0, (e['id'], hex(r))
            img[r:r + 2] = (new[int(a_hex, 16)] & 0xFFFF).to_bytes(2, 'little')
    for a_hex, offs in e.get('ptr_words', {}).items():   # plain 16-bit pointer words read by asm stubs
        for r in offs:
            r = int(r, 16)
            img[r:r + 2] = (new[int(a_hex, 16)] & 0xFFFF).to_bytes(2, 'little')
    for r in e.get('bank_refs', []):
        r = int(r, 16)
        assert img[r - 1] == 0xA9, (e['id'], hex(r))
        img[r] = bank
    for long_ref, addrs in e.get('tables', []):
        p = reloc[0]
        for k, a_hex in enumerate(addrs):
            img[p + 2 * k:p + 2 * k + 2] = (new[int(a_hex, 16)] & 0xFFFF).to_bytes(2, 'little')
        reloc[0] += 2 * len(addrs)
        r = int(long_ref, 16)
        img[r:r + 3] = to_cpu(p).to_bytes(3, 'little')


def build_ptrtables(e, rom, img, pre, reloc):
    """In-place 16-bit pointer tables (read as LDA abs,x in their own bank) whose strings move to the UI area.
    e: tables: [[file_off, count]], bank_refs: [LDA #bank operand offsets], line_cells, strings: {cpu_addr: text}.
    Text: '\\n' pads the line with blanks to line_cells; leading spaces of a line = that many blank cells."""
    new = {}
    for a_hex, text in e['strings'].items():
        cells = []
        lines = text.split('\n')
        for i, line in enumerate(lines):
            lead = len(line) - len(line.lstrip(' '))
            row = [BLANK] * lead
            if line.strip():
                cols = render(line.strip(), e['mode'])
                row += [pre.code(r) for r in cells_from_cols(cols, (len(cols) + 15) // 16)]
            if len(row) > e['line_cells']:
                raise ValueError('%s: %r is %d cells > %d' % (e['id'], line, len(row), e['line_cells']))
            if i < len(lines) - 1:
                row += [BLANK] * (e['line_cells'] - len(row))
            cells += row
        data = encode_cells(cells or [BLANK]) + b'\x00'
        p = reloc[0]
        img[p:p + len(data)] = data
        reloc[0] += len(data)
        new[int(a_hex, 16) & 0xFFFF] = to_cpu(p)
    banks = {v >> 16 for v in new.values()}
    assert len(banks) == 1, e['id']
    bank = banks.pop()
    for off_hex, n in e['tables']:
        off = int(off_hex, 16)
        for k in range(n):
            o = off + 2 * k
            old = rom[o] | rom[o + 1] << 8
            if old not in new:
                raise ValueError('%s: table %s[%d] -> %04X has no English' % (e['id'], off_hex, k, old))
            img[o:o + 2] = (new[old] & 0xFFFF).to_bytes(2, 'little')
    for r in e['bank_refs']:
        r = int(r, 16)
        assert img[r - 1] == 0xA9, (e['id'], hex(r))
        img[r] = bank


def load():
    return json.load(open(os.path.join(ROOT, 'ui', 'ui.json'), encoding='utf-8'))


RELOC_OFF, RELOC_END = 0x30E000, 0x310000   # $E1:E000-$E1:FFFF: relocated UI strings


def apply(img, rom, pre_off):
    """Write every UI string with English into img. Returns list of errors."""
    pre, errs = Pre(), []
    reloc = RELOC_OFF
    bank84_copy(img, rom)
    E2_ALLOC[0] = 0x317000
    for e in load():
        if not e.get('en') and not e.get('en_tsv') and e['kind'] not in ('screen', 'namelist', 'strset', 'ptrtables'):
            continue
        try:
            if e['kind'] == 'linear':
                off, nbytes, data = build_linear(e, rom, pre)
                # bank_refs may be shared by several strings (one draw routine), so those always relocate
                if len(data) <= nbytes and not e.get('bank_refs'):
                    img[off:off + nbytes] = data + b'\x00' * (nbytes - len(data))
                else:
                    # relocate: patch every `LDA #bank / STA $02 / LDY #ptr / STY $00` site listed in refs,
                    # or split sites: ptr_refs (LDY #imm16 operands) + bank_refs (LDA #bank operands)
                    if not e.get('refs') and not e.get('ptr_refs'):
                        raise ValueError('%s: %d bytes > %d and no refs to relocate' % (e['id'], len(data), nbytes))
                    if reloc + len(data) > RELOC_END:
                        raise ValueError('UI relocation area full')
                    img[reloc:reloc + len(data)] = data
                    cpu = ((reloc >> 15) + 0x80) << 16 | 0x8000 | (reloc & 0x7FFF)
                    for r in e.get('refs', []):
                        r = int(r, 16)
                        assert img[r] == 0xA9 and img[r + 2] == 0x85 and img[r + 4] == 0xA0, (e['id'], hex(r))
                        img[r + 1] = cpu >> 16
                        img[r + 5:r + 7] = (cpu & 0xFFFF).to_bytes(2, 'little')
                    for r in e.get('ptr_refs', []):
                        r = int(r, 16)
                        assert img[r - 1] == 0xA0, (e['id'], hex(r))
                        img[r:r + 2] = (cpu & 0xFFFF).to_bytes(2, 'little')
                    for r in e.get('bank_refs', []):
                        r = int(r, 16)
                        assert img[r - 1] == 0xA9 and img[r] in (rom[r], cpu >> 16), (e['id'], hex(r))
                        img[r] = cpu >> 16
                    img[off:off + nbytes] = bytes([BLANK]) * (nbytes - 1) + b'\x00'
                    reloc += len(data)
            elif e['kind'] == 'table':
                build_table(e, rom, img, pre)
            elif e['kind'] == 'bytes':   # literal in-place patch (same length)
                off, data = int(e['off'], 16), bytes.fromhex(e['hex'])
                assert len(data) == int(e['len']), e['id']
                img[off:off + len(data)] = data
            elif e['kind'] == 'dict':
                build_dict_names(e, rom, img, pre)
            elif e['kind'] in ('screen', 'namelist', 'strset', 'ptrtables'):
                rr = [reloc]
                {'screen': build_screen, 'namelist': build_namelist, 'strset': build_strset,
                 'ptrtables': build_ptrtables}[e['kind']](e, rom, img, pre, rr)
                reloc = rr[0]
                if reloc > RELOC_END:
                    raise ValueError('UI relocation area full')
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
