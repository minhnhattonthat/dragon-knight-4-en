"""Battle confirmation popups (BG1, lo-res 8x8 4bpp): "SAVE しますか?", "終了しますか?", "降伏しますか?",
"SAVE しました。". Block at C0:BE65 (file 0x203E65): 0x20-byte header (palette) + LZ tiles (118 tiles, loaded at
tile 0x380). Tilemaps: 16x8 words each at file 0x2A8C5 + 0x100*k, read by 84:90D8 (LDA #$C0 / LDY #$BE65).

The text rows are repainted (per-pixel-row background = most common index in that row of the text area, text in
the darkest text colour, bold font_en), every popup is re-tiled with dedup, and the new block goes to $E0:E000.

python -X utf8 tools/gfx_popups.py OUT.png   -> preview of the four popups (greyscale indices)
"""
import os
import sys
from collections import Counter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lz  # noqa: E402
from gfx_buttons import text_cols  # noqa: E402

BLOCK, LZ_AT = 0x203E65, 0x203E85
MAPS = [0x2A8C5 + 0x100 * k for k in range(4)]
# YES / NO highlighted button rows (16x2), drawn over popup rows 4-5 when the cursor moves (descriptors 85:A8B7)
BUTTONS = [0x2ACC5, 0x2AD05]
TILE0 = 0x380
NEW_AT, NEW_CPU = 0x306000, 0xE0E000          # $E0:E000-FFFF, free (engine code ends below $E0:E000)
LOADER = 0x210D8                              # LDA #$C0 / STA $47 / LDY #$BE65
# (popup, text rows, English)
# Short forms: the block holds at most 128 tiles (indices 0x380-0x3FF) and the gradient background makes every
# text tile unique.
TEXT = [(0, (1, 2), 'Save the game?'), (1, (1, 2), 'End this turn?'), (2, (1, 2), 'Yield?'),
        (3, (2, 3), 'Game saved.')]


def tile_px(t, i):
    b = t[i * 32:(i + 1) * 32]
    return [[(b[2 * y] >> (7 - x) & 1) | (b[2 * y + 1] >> (7 - x) & 1) << 1 | (b[16 + 2 * y] >> (7 - x) & 1) << 2 |
             (b[17 + 2 * y] >> (7 - x) & 1) << 3 for x in range(8)] for y in range(8)]


def tile_bytes(px):
    out = bytearray(32)
    for y in range(8):
        for x in range(8):
            v, m = px[y][x], 0x80 >> x
            for k, o in enumerate((2 * y, 2 * y + 1, 16 + 2 * y, 17 + 2 * y)):
                if v >> k & 1:
                    out[o] |= m
    return bytes(out)


def render_popup(rom, tiles, base, nrows=8):
    """16 x nrows tilemap at base -> (pixels [8*nrows][128], attrs [nrows][16] = palette/priority bits)"""
    px = [[0] * 128 for _ in range(8 * nrows)]
    attrs = [[0] * 16 for _ in range(nrows)]
    for r in range(nrows):
        for c in range(16):
            o = base + 2 * (r * 16 + c)
            w = rom[o] | rom[o + 1] << 8
            # tiles outside the block (blank/system tiles) keep their word; block tiles are re-tiled unflipped
            attrs[r][c] = ('raw', w) if (w & 0x3FF) < TILE0 else ('blk', w & 0x3C00)
            ti = (w & 0x3FF) - TILE0
            t = tile_px(tiles, ti) if 0 <= ti < len(tiles) // 32 else [[0] * 8] * 8
            for y in range(8):
                for x in range(8):
                    sy, sx = (7 - y if w & 0x8000 else y), (7 - x if w & 0x4000 else x)
                    px[r * 8 + y][c * 8 + x] = t[sy][sx]
    return px, attrs


def patch(rom):
    """-> {file_off: bytes} writes."""
    tiles, _ = lz.decompress(rom, LZ_AT)
    pops = [render_popup(rom, tiles, m) for m in MAPS] + [render_popup(rom, tiles, m, 2) for m in BUTTONS]
    for k, rows, text in TEXT:
        px = pops[k][0]
        y0, y1, x0, x1 = rows[0] * 8, rows[1] * 8 + 8, 2, 126
        # background is a 2-colour dither per pixel row; columns 1-2 (left of any text) hold its phase
        ink = Counter(v for y in range(y0, y1) for x in range(x0, x1)
                      for v in [px[y][x]] if v not in (px[y][1], px[y][2]))
        dark = ink.most_common(1)[0][0]
        for y in range(y0, y1):
            for x in range(x0, x1):
                px[y][x] = px[y][1 + (x - 1) % 2]
        cols = text_cols(text)
        if len(cols) > x1 - x0:
            raise SystemExit('popup text too wide: %r' % text)
        sx = x0 + (x1 - x0 - len(cols)) // 2
        top = y0 + (y1 - y0 - 12) // 2
        for i, col in enumerate(cols):
            for r in range(12):
                if col >> r & 1:
                    px[top + r][sx + i] = dark
    # re-tile with dedup
    new_tiles, index, maps = [], {}, {}
    for base, (px, attrs) in zip(MAPS + BUTTONS, pops):
        m = bytearray()
        for r in range(len(attrs)):
            for c in range(16):
                kind, a = attrs[r][c]
                if kind == 'blk':
                    t = [row[c * 8:c * 8 + 8] for row in px[r * 8:r * 8 + 8]]
                    for flip, v in ((0, t), (0x4000, [row[::-1] for row in t]), (0x8000, t[::-1]),
                                    (0xC000, [row[::-1] for row in t[::-1]])):
                        tb = tile_bytes(v)
                        if tb in index:
                            break
                    else:
                        flip, tb = 0, tile_bytes(t)
                        index[tb] = len(new_tiles)
                        new_tiles.append(tb)
                    w = a | flip | (TILE0 + index[tb])
                else:
                    w = a
                m += w.to_bytes(2, 'little')
        maps[base] = bytes(m)
    if len(new_tiles) > 0x400 - TILE0:
        raise SystemExit('popups: %d tiles > %d' % (len(new_tiles), 0x400 - TILE0))
    raw = b''.join(new_tiles)
    block = bytes(rom[BLOCK:LZ_AT]) + lz.compress(raw)
    if len(block) > 0x2000:
        raise SystemExit('popups: block too big')
    assert lz.decompress(block, 0x20)[0] == raw
    out = dict(maps)
    out[NEW_AT] = block
    assert rom[LOADER:LOADER + 2] == b'\xa9\xc0' and rom[LOADER + 4:LOADER + 7] == b'\xa0\x65\xbe'
    out[LOADER + 1] = bytes([NEW_CPU >> 16])
    out[LOADER + 5] = (NEW_CPU & 0xFFFF).to_bytes(2, 'little')
    return out


if __name__ == '__main__':
    from PIL import Image
    from dk4 import load_rom
    rom = bytearray(load_rom()).ljust(0x400000, b'\xff')
    for off, data in patch(rom).items():
        rom[off:off + len(data)] = data
    tiles, _ = lz.decompress(rom, NEW_AT + 0x20)
    img = Image.new('L', (128 * 4 + 12, 64))
    for k in range(4):
        px, _ = render_popup(rom, tiles, MAPS[k])
        for y in range(64):
            for x in range(128):
                img.putpixel((k * 131 + x, y), px[y][x] * 16)
    print(len(tiles) // 32, 'tiles')
    img.resize((img.width * 3, img.height * 3), Image.NEAREST).save(sys.argv[1])
