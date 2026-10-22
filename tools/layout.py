"""English text -> far-text bytes for the dialogue box, mirroring the asm cell composer exactly (asm/dk4.asm).

Box: 3 lines of 24 cells (16 hi-res px each). The composer packs letters into cells; a letter that crosses a
cell edge is carried into the next cell; at a line end with a pending carry a FLUSH byte (0x7F) adds one cell.
Bytes: 0x20-0x7E letters, 0x7F flush, 0x00 newline (line+1; the 3rd newline of a page waits for a key and clears),
0x11 blank cell, 2-byte JP glyph codes (01-0F xx), 10 05 pp portrait, 0E FF end of far text.
"""
import os
import re
from dk4 import ROOT
from font_en import widths

W = widths()
CELLS = 24
LINES = 3
FLUSH = 0x7F
NL = 0x00
BLANK = 0x11
END = b'\x0e\xff'
JP_LBR, JP_RBR = 0x65A, 0x65C   # 【 】
INDENT = ' '


class LayoutError(Exception):
    pass


def cells_of(s):
    """(bytes, cells) for a run of ASCII letters starting at a cell edge with no carry; ends flushed."""
    out, cells, i, n = bytearray(), 0, 0, len(s)
    carry = None  # (width, x)
    while i < n or carry:
        x = 0
        if carry:
            x = carry[1] + carry[0]
            carry = None
            if i >= n:
                out.append(FLUSH)
                cells += 1
                break
        while True:
            c = s[i]
            if c not in W:
                raise LayoutError('no glyph for %r' % c)
            out.append(ord(c))
            i += 1
            before = x
            x += W[c]
            if x == 16:
                break
            if x > 16:
                carry = (W[c], before - 16)
                break
            if i >= n:
                break
        cells += 1
    return bytes(out), cells


def line_cells(s):
    return cells_of(s)[1] if s else 0


# The box interior ends 9 px into cell 24 (cells start at x=120 hi-res, the frame starts at x=496), so a full
# 24-cell line loses its last letter under the frame. Measured in-game (work/qa/deploy, Eto "Lushifon's").
MAX_PX = 376


def line_px(s):
    return sum(W[c] for c in s)


def wrap(text, first_budget=CELLS, budget=CELLS, indent=INDENT, first_indent=None):
    """Greedy word wrap by cells. Returns list of line strings (each including the indent).
    first_indent: prefix of the first line instead of indent (a mid-line continuation); if the first word
    does not fit there, the first line is just that prefix and the text starts on the next line."""
    words = text.split(' ')
    lines, cur = [], indent if first_indent is None else first_indent
    empty = True
    for w in words:
        if w == '':
            continue
        cand = cur + (w if empty else ' ' + w)
        lim = first_budget if not lines else budget
        if line_cells(cand) <= lim and (lim < CELLS or line_px(cand) <= MAX_PX):
            cur, empty = cand, False
        else:
            if empty and (lines or first_indent is None):
                raise LayoutError('word too long: %r' % w)
            lines.append(cur)
            cur, empty = indent + w, False
            if line_cells(cur) > budget:
                raise LayoutError('word too long: %r' % w)
    if not empty:
        lines.append(cur)
    return lines


SENT_END = re.compile(r'(?<=[.!?])\s+|(?<=[.!?]["\')])\s+')


def pages_of(text, per_page):
    """Wrap text into pages of per_page lines, breaking pages at sentence ends when that costs no extra page;
    a sentence longer than a page is broken inside it and the following sentences continue after its last line."""
    pages, cur = [], ''
    for s in SENT_END.split(text):
        cand = (cur + ' ' + s).strip()
        if len(wrap(cand)) <= per_page:
            cur = cand
            continue
        if cur:
            pages.append(wrap(cur))
        ls = wrap(s)
        while len(ls) > per_page:
            pages.append(ls[:per_page])
            ls = ls[per_page:]
        cur = ' '.join(x.strip() for x in ls)
    if cur:
        pages.append(wrap(cur))
    lines = wrap(text)
    if len(pages) > -(-len(lines) // per_page):   # sentence breaks would cost a page: fill pages instead
        pages = [lines[i:i + per_page] for i in range(0, len(lines), per_page)]
    return pages


def _name(name_en, portrait):
    if portrait is not None:
        pre = bytes([0x10, 0x05, portrait])
    else:
        pre = b''
    b, c = cells_of('{' + name_en + '}')   # { } = VWF name-tag brackets
    if c > CELLS:
        raise LayoutError('name too long: %r' % name_en)
    return pre + b


class Box:
    """Emits bytes while tracking the line within the page (0..2)."""

    def __init__(self, line=0):
        self.b = bytearray()
        self.line = line
        self.col_used = False   # something drawn on the current line
        self.col = 0            # cells drawn on the current line by text_line

    def nl(self):
        if not self.col_used:
            self.b.append(BLANK)  # 00 on an empty line is ignored by the game (80:B2F9): occupy a cell first
        self.b.append(NL)
        self.line = (self.line + 1) % LINES
        self.col_used = False
        self.col = 0

    def new_page(self):
        if self.line != 0 or self.col_used:
            while True:
                self.nl()
                if self.line == 0:
                    break

    def text_line(self, s):
        b, c = cells_of(s)
        if c > CELLS or line_px(s) > MAX_PX:
            raise LayoutError('line over %d cells / %d px (%d): %r' % (CELLS, MAX_PX, c, s))
        self.b += b
        self.col_used = True
        self.col += c

    def raw(self, b, used=True):
        self.b += b
        self.col_used = self.col_used or used


def dlg_region(segs, start_line=0, trailing_nl=False, first_budget=CELLS, attach=False, last_room=0):
    """segs: [(speaker_en or '', portrait or None, english text)]. Returns (bytes, end_line, end_col).
    first_budget: cells for the very first line when the region starts mid-line (after an inserted name or number).
    end_col: text cells on the last line (0 after a trailing newline)."""
    box = Box(start_line)
    for si, (name, portrait, text) in enumerate(segs):
        if name:
            box.new_page()
            box.raw(_name(name, portrait))
            box.nl()
        elif portrait is not None:
            box.raw(bytes([0x10, 0x05, portrait]), used=False)
        fb = first_budget if si == 0 and not name else CELLS
        if fb == 0 and text:   # mid-line with unknown room left: continue on the next line
            box.nl()
            fb = CELLS
        # after an inline number the text attaches directly: its own leading space (" points") or none ("!!")
        fi = (' ' if text[:1] == ' ' else '') if attach and si == 0 and not name else None
        lines = wrap(text, fb, first_indent=fi) if text else []
        if last_room and si == len(segs) - 1 and len(lines[-1:]) and line_cells(lines[-1]) > CELLS - last_room:
            head, _, w = lines[-1].rpartition(' ')   # the number after this region would not fit: move a word down
            if not head.strip():
                raise LayoutError('no room for the number after %r' % lines[-1])
            lines[-1:] = [head, INDENT + w]
        if name and len(lines) > LINES - 1:
            # overflow pages repeat the speaker; break them at sentence ends, not mid-sentence
            pages = pages_of(text, LINES - 1)
            for pi, pg in enumerate(pages):
                if pi:
                    box.new_page()
                    box.raw(_name(name, portrait))
                    box.nl()
                for j, ln in enumerate(pg):
                    box.text_line(ln)
                    if j != len(pg) - 1 or pi != len(pages) - 1:
                        box.nl()
            lines = []
        for j, ln in enumerate(lines):
            if box.line == 0 and not box.col_used and name and j > 0:
                box.raw(_name(name, portrait))  # repeat the speaker on continuation pages
                box.nl()
            box.text_line(ln)
            last = j == len(lines) - 1
            if not last:
                box.nl()
        # an unnamed segment after this one continues on the next line; a named one starts a new page
        if si != len(segs) - 1 and not segs[si + 1][0]:
            box.nl()
    if trailing_nl:
        box.nl()
    return bytes(box.b), box.line, box.col


def choice_region(lines_fields, jp_layout):
    """lines_fields: English [[field, ...] per line]; jp_layout: [[(start_cell, jp_cells_until_next)] per line]
    plus leading blank counts. Each English field starts at the JP field's cell."""
    out = bytearray()
    for li, (fields, lay) in enumerate(zip(lines_fields, jp_layout)):
        cell = 0
        for (start, avail), f in zip(lay, fields):
            if start < cell:
                raise LayoutError('choice field overlaps: %r' % f)
            out += bytes([BLANK]) * (start - cell)
            cell = start
            b, c = cells_of(f)
            if avail is not None and c > avail:
                raise LayoutError('choice field %r needs %d cells, %d free' % (f, c, avail))
            out += b
            cell += c
        if cell > CELLS:
            raise LayoutError('choice line over width')
        if li != len(lines_fields) - 1:
            out.append(NL)
    return bytes(out)


if __name__ == '__main__':
    for s in ['The quick brown fox jumps over the lazy dog.', 'Hello', 'mmmmmmmmmm', 'iiiiiiiiiiiiiiii']:
        b, c = cells_of(s)
        print(c, len(s), b)
    print(wrap("I'm Kakeru, son of Takeru and Luna. Nice to meet you! I hope we can be friends for a long time."))
