"""Turn a region (list of codes) into translation units.

Token kinds: ('name', dict_code, jp_name, portrait) | ('portrait', dict_code, value) | ('nl',) | ('blank',) |
             ('ch', jp_char) (a glyph or a non-name dictionary entry expanded char by char)
Region forms:
  dlg    : segments split at name tags; each segment = speaker + free text (wrapped by the builder)
  choice : choice-menu option lines (prev/next op 03 or 0C, or column layout); lines kept, fields at fixed cells
"""
from dk4 import load_rom, load_glyphs, dict_entries

_dict = None


def dict_tokens(rom, glyphs):
    """dict code -> ('name', jp, portrait) | ('portrait', value) | ('text', [codes])"""
    global _dict
    if _dict is not None:
        return _dict
    _dict = {}
    for code, a, raw in dict_entries(rom):
        i, portrait, codes = 0, None, []
        while i < len(raw) - 1:
            b = raw[i]
            if b == 0x10:
                assert raw[i + 1] == 0x05, (hex(code), raw.hex())
                portrait = raw[i + 2]
                i += 3
                continue
            if b < 0x10:
                codes.append(b << 8 | raw[i + 1])
                i += 2
            else:
                codes.append(b)
                i += 1
        if codes and codes[0] == 0x65A:  # 【name】
            jp = ''.join(glyphs[c] for c in codes[1:-1])
            _dict[code] = ('name', jp, portrait)
        elif portrait is not None and not codes:
            _dict[code] = ('portrait', portrait)
        else:
            assert portrait is None, hex(code)
            _dict[code] = ('text', codes)
    return _dict


def tokens(codes, rom, glyphs):
    d = dict_tokens(rom, glyphs)
    out = []
    for c in codes:
        if c == 0:
            out.append(('nl',))
        elif c == 0x11:
            out.append(('blank',))
        elif c >= 0x6CC:
            t = d[c]
            if t[0] == 'name':
                out.append(('name', c, t[1], t[2]))
            elif t[0] == 'portrait':
                out.append(('portrait', c, t[1]))
            else:
                for cc in t[1]:
                    out.append(('blank',) if cc == 0x11 else ('ch', glyphs[cc].rstrip('*')))
        else:
            out.append(('ch', glyphs[c].rstrip('*')))
    return out


def lines_of(toks):
    """Split tokens into lines (list of token lists) at 'nl'."""
    lines, cur = [], []
    for t in toks:
        if t[0] == 'nl':
            lines.append(cur)
            cur = []
        else:
            cur.append(t)
    lines.append(cur)
    return lines


def line_text(line):
    """JP text of a line: leading blanks dropped, inner blanks as full-width spaces."""
    s, started = [], False
    for t in line:
        if t[0] == 'blank':
            if started:
                s.append('　')
        elif t[0] == 'ch':
            started = True
            s.append(t[1])
    return ''.join(s).rstrip('　')


def is_choice(region, toks):
    """Option lines of a choice menu: 10 03 xx toggles option colour, 10 0C opens the menu."""
    if region['prev_op'] == 0x03 or region['next_op'] in (0x03, 0x0C):
        return not any(t[0] in ('name', 'portrait') for t in toks)
    return False


def choice_fields(line):
    """Fields of a choice line: [(start_cell, jp_text, cells_until_next_or_None)] split at runs of >= 2 blanks."""
    fields, cell, cur, cur_start, blanks = [], 0, [], None, 0
    for t in line:
        if t[0] == 'blank':
            blanks += 1
            if blanks >= 2 and cur:
                fields.append([cur_start, ''.join(cur)])
                cur, cur_start = [], None
            cell += 1
        else:
            if blanks == 1 and cur:
                cur.append('　')
            blanks = 0
            if cur_start is None:
                cur_start = cell
            cur.append(t[1])
            cell += 1
    if cur:
        fields.append([cur_start, ''.join(cur)])
    return fields


def units(region, rom, glyphs):
    """Translation units of a region: list of dicts {sid, form, speaker, portrait, jp, lines}."""
    toks = tokens(region['codes'], rom, glyphs)
    if is_choice(region, toks):
        ls = [l for l in (' | '.join(f[1] for f in choice_fields(x)) for x in lines_of(toks)) if l]
        return [{'sid': 0, 'form': 'choice', 'speaker': '', 'jp': ' / '.join(ls), 'nlines': len(ls)}]
    segs, cur = [], None
    for t in toks:
        if t[0] == 'name':
            cur = {'speaker': t[2], 'toks': []}
            segs.append(cur)
            continue
        if cur is None:
            cur = {'speaker': '', 'toks': []}
            segs.append(cur)
        cur['toks'].append(t)
    out = []
    for i, s in enumerate(segs):
        ls = [line_text(l) for l in lines_of(s['toks'])]
        while ls and ls[0] == '' and s['speaker']:
            ls.pop(0)  # the newline right after the name tag
        jp = ' / '.join(l for l in ls if l != '')
        out.append({'sid': i, 'form': 'dlg' if jp else 'empty', 'speaker': s['speaker'], 'jp': jp,
                    'nlines': len([l for l in ls if l != ''])})
    return out
