"""Combat-screen name plates (BG1, lo-res 8x8 4bpp). The game draws each name one 8x8 kana tile per character
(packed half-width katakana list at 82:C6BB, routine 82:87D0, font LZ block 82:CCD3 -> 7F:D800). English names are
proportional, up to 64 px: every name is precomposed here into 8 tiles, and asm/dk4.asm (plate_font) copies the
player's and the enemy's into font tiles 0x60-0x67 / 0x68-0x6F (kana ﾀ-ﾏ, unused once no name draws kana; 0x41-0x43
are the stat icons) right after the font is decompressed. plate_ptrs makes 82:87D0 draw those fixed tiles
(codes $C0-$C7 / $C8-$CF) instead of the kana string.

Per name: 8 tiles x 8 rows x (body mask, shadow mask) = 128 bytes at $FF:8000 + 128 * packed index.
Body = colour $D, shadow (+1,+1) = $E, background = $6 (rows 0-3) / $7 (rows 4-7), as the game's own glyphs.

python -X utf8 tools/gfx_plates.py          -> prints every name with its width (fails on a name over 64 px)
"""
import os
import sys
import unicodedata
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TABLE, STR_END = 0x146BB, 0x1485B   # packed name pointers (82:C6BB) / first string = end of the table
LZ_AT = 0x14CD3                     # font block; also the end pointer of the last name
COUNT = (STR_END - TABLE) // 2      # 208: index 0 = blank, allies 1-31, enemies = 0x20 + enemy id
DATA_OFF = 0x3F8000                 # $FF:8000
FIXED_OFF = STR_END                 # 82:C85B: codes $C0-$CF, the strings plate_ptrs points 82:87D0 at
WIDTH = 64

# rows 0-7; caps rows 0-5, x-height rows 2-5, descenders rows 6-7 (shadow falls on row 6)
G = {
    ' ': ['..'],
    "'": ['#', '#'],
    '-': ['..', '..', '..', '##'],
    '.': ['.', '.', '.', '.', '.', '#'],
    'A': ['.##.', '#..#', '#..#', '####', '#..#', '#..#'],
    'B': ['###.', '#..#', '###.', '#..#', '#..#', '###.'],
    'C': ['.###', '#...', '#...', '#...', '#...', '.###'],
    'D': ['###.', '#..#', '#..#', '#..#', '#..#', '###.'],
    'E': ['####', '#...', '###.', '#...', '#...', '####'],
    'F': ['####', '#...', '###.', '#...', '#...', '#...'],
    'G': ['.###', '#...', '#...', '#.##', '#..#', '.###'],
    'H': ['#..#', '#..#', '####', '#..#', '#..#', '#..#'],
    'I': ['###', '.#.', '.#.', '.#.', '.#.', '###'],
    'J': ['..##', '...#', '...#', '...#', '#..#', '.##.'],
    'K': ['#..#', '#.#.', '##..', '#.#.', '#..#', '#..#'],
    'L': ['#...', '#...', '#...', '#...', '#...', '####'],
    'M': ['#...#', '##.##', '#.#.#', '#...#', '#...#', '#...#'],
    'N': ['#..#', '##.#', '#.##', '#..#', '#..#', '#..#'],
    'O': ['.##.', '#..#', '#..#', '#..#', '#..#', '.##.'],
    'P': ['###.', '#..#', '#..#', '###.', '#...', '#...'],
    'Q': ['.##.', '#..#', '#..#', '#..#', '#.#.', '.#.#'],
    'R': ['###.', '#..#', '#..#', '###.', '#.#.', '#..#'],
    'S': ['.###', '#...', '.##.', '...#', '...#', '###.'],
    'T': ['#####', '..#..', '..#..', '..#..', '..#..', '..#..'],
    'U': ['#..#', '#..#', '#..#', '#..#', '#..#', '.##.'],
    'V': ['#...#', '#...#', '#...#', '.#.#.', '.#.#.', '..#..'],
    'W': ['#...#', '#...#', '#.#.#', '#.#.#', '##.##', '#...#'],
    'X': ['#...#', '.#.#.', '..#..', '..#..', '.#.#.', '#...#'],
    'Y': ['#...#', '.#.#.', '..#..', '..#..', '..#..', '..#..'],
    'Z': ['####', '...#', '..#.', '.#..', '#...', '####'],
    'a': ['....', '....', '.###', '#..#', '#..#', '.###'],
    'b': ['#...', '#...', '###.', '#..#', '#..#', '###.'],
    'c': ['...', '...', '.##', '#..', '#..', '.##'],
    'd': ['...#', '...#', '.###', '#..#', '#..#', '.###'],
    'e': ['....', '....', '.##.', '####', '#...', '.###'],
    'f': ['..#', '.#.', '###', '.#.', '.#.', '.#.'],
    'g': ['....', '....', '.###', '#..#', '#..#', '.###', '...#', '.##.'],
    'h': ['#...', '#...', '###.', '#..#', '#..#', '#..#'],
    'i': ['#', '.', '#', '#', '#', '#'],
    'j': ['.#', '..', '.#', '.#', '.#', '.#', '.#', '#.'],
    'k': ['#..', '#..', '#.#', '##.', '#.#', '#.#'],
    'l': ['#', '#', '#', '#', '#', '#'],
    'm': ['.....', '.....', '####.', '#.#.#', '#.#.#', '#.#.#'],
    'n': ['....', '....', '###.', '#..#', '#..#', '#..#'],
    'o': ['....', '....', '.##.', '#..#', '#..#', '.##.'],
    'p': ['....', '....', '###.', '#..#', '#..#', '###.', '#...', '#...'],
    'q': ['....', '....', '.###', '#..#', '#..#', '.###', '...#', '...#'],
    'r': ['...', '...', '#.#', '##.', '#..', '#..'],
    's': ['...', '...', '.##', '#..', '..#', '##.'],
    't': ['.#.', '.#.', '###', '.#.', '.#.', '..#'],
    'u': ['....', '....', '#..#', '#..#', '#..#', '.###'],
    'v': ['...', '...', '#.#', '#.#', '#.#', '.#.'],
    'w': ['.....', '.....', '#...#', '#.#.#', '#.#.#', '.#.#.'],
    'x': ['...', '...', '#.#', '.#.', '.#.', '#.#'],
    'y': ['....', '....', '#..#', '#..#', '#..#', '.###', '...#', '.##.'],
    'z': ['...', '...', '###', '..#', '.#.', '###'],
}


def jp_names(rom):
    """Packed half-width katakana names, NFKC-normalised to full-width; index 0 is the blank entry."""
    ptrs = [rom[TABLE + 2 * k] | rom[TABLE + 2 * k + 1] << 8 for k in range(COUNT)] + [0x8000 | LZ_AT & 0x7FFF]
    out = []
    for k in range(COUNT):
        raw = rom[0x10000 + (ptrs[k] & 0x7FFF):0x10000 + (ptrs[k + 1] & 0x7FFF)]
        out.append(unicodedata.normalize('NFKC', ''.join(chr(0xFF61 + c - 0xA1) if c >= 0xA1 else chr(c)
                                                         for c in raw)).strip())
    return out


PLATE_ONLY = {'アンデッド': 'Undead'}   # packed 202; the bank-$84 table has カロン (a dictionary code) there


def en_names(rom):
    """English per packed index: ui/enemy_names.tsv (bank-$84 name table index = packed index - 1) when its
    Japanese matches, else the speaker names in tbl/names_en.tsv by Japanese, else PLATE_ONLY."""
    def norm(s):
        return s.replace('へ', 'ヘ')   # the 16x16 glyph table reads ヘ as hiragana
    tsv, spk = {}, dict(PLATE_ONLY)
    for ln in open(os.path.join(ROOT, 'ui', 'enemy_names.tsv'), encoding='utf-8'):
        if ln.strip():
            i, jp, en = ln.rstrip('\n').split('\t')
            tsv[int(i)] = (norm(jp), en)
    for ln in open(os.path.join(ROOT, 'tbl', 'names_en.tsv'), encoding='utf-8'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 2:
            spk.setdefault(norm(p[0]), p[1])
    out = []
    for k, jp in enumerate(jp_names(rom)):
        t = tsv.get(k - 1)
        en = '' if not jp else t[1] if t and t[0] == jp else spk.get(jp)
        if en is None:
            raise ValueError('plate name %d %s: no English (ui/enemy_names.tsv row %d)' % (k, jp, k - 1))
        out.append(en)
    return out


def body(text):
    """8 rows of a WIDTH-px mask (bit WIDTH-1 = leftmost px); the pen starts at x=1, letters 1 px apart."""
    rows, x = [0] * 8, 1
    for ch in text:
        g = G[ch]
        w = len(g[0])
        for y, r in enumerate(g):
            for i, c in enumerate(r):
                if c == '#':
                    rows[y] |= 1 << (WIDTH - 1 - x - i)
        x += w + 1
    if x > WIDTH:   # the last letter's shadow column may use the gap
        raise ValueError('plate name %r is %d px, max %d' % (text, x - 1, WIDTH))
    return rows


def name_data(text):
    b = body(text)
    s = [((b[y - 1] >> 1) if y else 0) & ~b[y] & (1 << WIDTH) - 1 for y in range(8)]
    out = bytearray()
    for t in range(WIDTH // 8):
        sh = WIDTH - 8 - 8 * t
        for y in range(8):
            out += bytes((b[y] >> sh & 0xFF, s[y] >> sh & 0xFF))
    return out


def patch(rom):
    data = b''.join(name_data(n) for n in en_names(rom))
    assert len(data) <= 0x7000   # $FF:F000 = plate code (asm/dk4.asm)
    return {DATA_OFF: data, FIXED_OFF: bytes(range(0xC0, 0xD0))}


if __name__ == '__main__':
    rom = open(os.path.join(ROOT, 'rom', 'Dragon Knight 4 (Japan).sfc'), 'rb').read()
    for k, (jp, en) in enumerate(zip(jp_names(rom), en_names(rom))):
        b = body(en)
        w = max((WIDTH - (r & -r).bit_length() + 1) if r else 0 for r in b)
        print(k, jp, en, w)
