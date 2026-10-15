"""Battle command buttons (OBJ, 4bpp raw at ROM 0x4DABC, 96 tiles = 16x6 tiles of 8x8):
3 rows of 4 buttons, each button 4x2 tiles (32x16 px): [Wait Wait Attack Attack] [Heal Heal Break Break]
[YES YES NO NO] (normal / highlighted). The kanji are erased (each pixel row refilled with that row's background
colour) and English is drawn in the text colour with a bold 1-px font.

python -X utf8 tools/gfx_buttons.py OUT.png   -> preview (greyscale indices x 32)
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import font_en

OFF, NT = 0x4DABC, 96
LABELS = [['Wait', 'Wait', 'Attack', 'Attack'], ['Heal', 'Heal', 'Break', 'Break'], [None, None, None, None]]


def decode(data):
    """-> 2D list [48][128] of colour indices."""
    px = [[0] * 128 for _ in range(48)]
    for t in range(NT):
        tx, ty = (t % 16) * 8, (t // 16) * 8
        b = data[t * 32:(t + 1) * 32]
        for y in range(8):
            p0, p1, p2, p3 = b[2 * y], b[2 * y + 1], b[16 + 2 * y], b[17 + 2 * y]
            for x in range(8):
                m = 0x80 >> x
                px[ty + y][tx + x] = (p0 & m and 1) | (p1 & m and 2) | (p2 & m and 4) | (p3 & m and 8)
    return px


def encode(px):
    out = bytearray(NT * 32)
    for t in range(NT):
        tx, ty = (t % 16) * 8, (t // 16) * 8
        for y in range(8):
            p = [0, 0, 0, 0]
            for x in range(8):
                v = px[ty + y][tx + x]
                for k in range(4):
                    if v >> k & 1:
                        p[k] |= 0x80 >> x
            out[t * 32 + 2 * y], out[t * 32 + 2 * y + 1] = p[0], p[1]
            out[t * 32 + 16 + 2 * y], out[t * 32 + 17 + 2 * y] = p[2], p[3]
    return bytes(out)


def text_cols(text):
    cols = []
    for ch in text:
        body, desc = font_en.G[ch]
        for cx in range(len(body[0])):
            col = 0
            for r, line in enumerate(body + (desc or [])):
                if line[cx] == '#':
                    col |= 1 << r
            cols.append(col)
        cols.append(0)
    while cols and cols[-1] == 0:
        cols.pop()
    # bold: OR each column into the next
    bold = cols + [0]
    for i in range(len(cols)):
        bold[i + 1] |= cols[i]
    return bold


def patch(rom_bytes):
    px = decode(rom_bytes[OFF:OFF + NT * 32])
    for br, row in enumerate(LABELS):
        for bc, label in enumerate(row):
            if label is None:
                continue
            x0, y0 = bc * 32, br * 16
            # row background = most common index in that pixel row of the button; text = most common other index
            from collections import Counter
            # the 2 px at each edge never carry text: their colour is the row's background gradient
            bgs = [Counter([px[y0 + y][x0], px[y0 + y][x0 + 1], px[y0 + y][x0 + 30], px[y0 + y][x0 + 31]])
                   .most_common(1)[0][0] for y in range(16)]
            other = Counter()
            for y in range(16):
                for x in range(2, 30):
                    v = px[y0 + y][x0 + x]
                    if v != bgs[y]:
                        other[v] += 1
            text = other.most_common(1)[0][0]
            bgs = [px[y0 + y][x0 + 1] for y in range(16)]
            for y in range(16):
                for x in range(32):
                    px[y0 + y][x0 + x] = bgs[y]
            cols = text_cols(label)
            if len(cols) > 32:
                raise SystemExit('button label too wide: %r' % label)
            sx = x0 + (32 - len(cols)) // 2
            for i, col in enumerate(cols):
                for r in range(12):
                    if col >> r & 1:
                        px[y0 + 2 + r][sx + i] = text
    return encode(px)


if __name__ == '__main__':
    from PIL import Image
    from dk4 import load_rom
    rom = load_rom()
    data = patch(rom)
    px = decode(data)
    img = Image.new('L', (128, 48))
    for y in range(48):
        for x in range(128):
            img.putpixel((x, y), px[y][x] * 16)
    img.resize((512, 192), Image.NEAREST).save(sys.argv[1])
