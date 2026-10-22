"""Copy the last frame of each dialogue page (the frame before the text box clears) into DIR/pages/.

python -X utf8 tools/debug/pages.py RUN_DIR [FROM_FRAME]   (RUN_DIR = an emu.py --shot-every 5..10 --mash run)
Then: sheet.py RUN_DIR/pages --from A --to B --crop 0,330,512,118   (16 pages per sheet)
"""
import glob
import os
import shutil
import sys

from PIL import Image

d = sys.argv[1]
start = int(sys.argv[2]) if len(sys.argv) > 2 else 0
fs = sorted(f for f in glob.glob(os.path.join(d, 'f[0-9]*.png')) if int(os.path.basename(f)[1:7]) >= start)
out = os.path.join(d, 'pages')
shutil.rmtree(out, ignore_errors=True)
os.makedirs(out)


def ink(f):
    """Bright pixels inside the text box (hi-res 512x448 shot)."""
    im = Image.open(f).convert('L').crop((110, 340, 500, 440))
    return sum(1 for p in im.getdata() if p > 160)


prev = None
for f in fs:
    n = ink(f)
    if prev and prev[0] > 200 and n < prev[0] * 0.5:
        shutil.copy(prev[1], out)
    prev = (n, f)
print(len(os.listdir(out)))
