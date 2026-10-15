"""Render chosen glyph codes large, side by side: glyph_pairs.py ROM OUT.png CODE[,CODE..] ..."""
import os
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font import decode_glyph

rom = open(sys.argv[1], 'rb').read()
groups = [[int(c, 16) for c in g.split(',')] for g in sys.argv[3:]]
S = 5
W = max(len(g) for g in groups)
img = Image.new('RGB', (W * 18 * S + 60, len(groups) * 17 * S), 'white')
dr = ImageDraw.Draw(img)
for gy, g in enumerate(groups):
    for gx, code in enumerate(g):
        cx, cy = 60 + gx * 18 * S, gy * 17 * S
        dr.text((cx, cy + 70), '%03X' % code, fill='red')
        rows = decode_glyph(rom, code - 0x11)
        for r in range(14):
            for x in range(16):
                if rows[r] & (0x8000 >> x):
                    dr.rectangle([cx + x * S, cy + r * S, cx + x * S + S - 1, cy + r * S + S - 1], fill='black')
img.save(sys.argv[2])
