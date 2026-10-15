"""Render the dialogue font as labelled sheets for transcription: font_sheet.py ROM OUTDIR [per_image=256] [cols=16]."""
import os
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from font import decode_glyph

rom = open(sys.argv[1], 'rb').read()
outdir = sys.argv[2]
per = int(sys.argv[3]) if len(sys.argv) > 3 else 256
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 16
first = int(sys.argv[5], 16) if len(sys.argv) > 5 else 0
N = 0x6CC - 0x11
os.makedirs(outdir, exist_ok=True)
S = 3
for start in range(first, N, per):
    n = min(per, N - start)
    rows = (n + cols - 1) // cols
    img = Image.new('RGB', (40 + cols * 18 * S, rows * 17 * S), 'white')
    dr = ImageDraw.Draw(img)
    for k in range(n):
        i = start + k
        cx, cy = 40 + (k % cols) * 18 * S, (k // cols) * 17 * S
        if k % cols == 0:
            dr.text((2, cy + 15), '%03X' % (i + 0x11), fill='red')
        g = decode_glyph(rom, i)
        for r in range(14):
            for x in range(16):
                if g[r] & (0x8000 >> x):
                    dr.rectangle([cx + x * S, cy + r * S, cx + x * S + S - 1, cy + r * S + S - 1], fill='black')
        dr.rectangle([cx - 1, cy - 1, cx + 16 * S, cy + 14 * S], outline=(200, 200, 255))
    img.save(os.path.join(outdir, 'font_%03X.png' % (start + 0x11)))
