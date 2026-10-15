"""Dragon Knight 4 (SFC) dialogue font: 1bpp 16x14 glyphs, 28 bytes each, at ROM 0x40000.

Layout per glyph: bytes 0-7 = left 8px rows 0-7, 8-15 = right rows 0-7, 16-21 = left rows 8-13, 22-27 = right rows 8-13.
Glyph index = text code - 0x11. The glyph routine (80AEAE) moves to the next bank after 0x492 glyphs (0x7FF8 bytes).
"""
FONT_OFF = 0x40000
PER_BANK = 0x492
GLYPH_W, GLYPH_H = 16, 14


def glyph_off(idx):
    return FONT_OFF + (idx // PER_BANK) * 0x8000 + (idx % PER_BANK) * 28


def decode_glyph(rom, idx):
    """Return 14 rows of 16-bit ints (bit 15 = leftmost pixel)."""
    g = rom[glyph_off(idx):glyph_off(idx) + 28]
    rows = []
    for r in range(14):
        if r < 8:
            lo, hi = g[r], g[8 + r]
        else:
            lo, hi = g[16 + r - 8], g[22 + r - 8]
        rows.append(lo << 8 | hi)
    return rows


def encode_glyph(rows):
    b = bytearray(28)
    for r in range(14):
        lo, hi = rows[r] >> 8 & 0xFF, rows[r] & 0xFF
        if r < 8:
            b[r], b[8 + r] = lo, hi
        else:
            b[16 + r - 8], b[22 + r - 8] = lo, hi
    return bytes(b)
