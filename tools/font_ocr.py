"""Map game glyphs to Unicode by matching against MS Gothic renders (one-off recon helper).

python -X utf8 tools/font_ocr.py ROM OUT.tsv
Writes idx<TAB>code<TAB>char<TAB>score<TAB>second-best for every glyph; verify low-margin rows by eye.
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, __file__.rsplit('\\', 1)[0].rsplit('/', 1)[0])
from font import decode_glyph

N = 0x6CC - 0x11


def candidates():
    cs = set()
    for hi in range(0x81, 0xA0):
        for lo in range(0x40, 0xFD):
            try:
                cs.add(bytes([hi, lo]).decode('shift_jis'))
            except UnicodeDecodeError:
                pass
    for hi in range(0xE0, 0xEB):
        for lo in range(0x40, 0xFD):
            try:
                cs.add(bytes([hi, lo]).decode('shift_jis'))
            except UnicodeDecodeError:
                pass
    cs.update('①②③④⑤⑥⑦⑧⑨⑩♪♥〜～')
    return sorted(c for c in cs if len(c) == 1 and not c.isspace())


def blur(a):
    k = np.array([0.25, 0.5, 0.25], np.float32)
    a = np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 0, a)
    return np.apply_along_axis(lambda r: np.convolve(r, k, 'same'), 1, a)


def render(fonts, ch):
    outs = []
    for f in fonts:
        img = Image.new('L', (64, 64), 0)
        ImageDraw.Draw(img).text((0, 0), ch, font=f, fill=255)
        a = np.array(img.resize((16, 16), Image.BOX), dtype=np.float32) / 255
        outs.append(blur(a))
    return outs


def norm(a):
    ys, xs = np.nonzero(a)
    if len(ys) == 0:
        return None
    return a


def main():
    rom = open(sys.argv[1], 'rb').read()
    fonts = [ImageFont.truetype('C:/Windows/Fonts/msgothic.ttc', 56),
             ImageFont.truetype('C:/Windows/Fonts/YuGothB.ttc', 56)]
    cands = candidates()
    refs = []  # (char, array 16x16 float)
    for c in cands:
        for a in render(fonts, c):
            if a.sum():
                refs.append((c, a.astype(np.float32)))
    R = np.stack([r[1] for r in refs])  # K,16,16
    R = R - R.mean(axis=(1, 2), keepdims=True)
    R /= np.sqrt((R * R).sum(axis=(1, 2), keepdims=True)) + 1e-6
    names = [r[0] for r in refs]
    out = open(sys.argv[2], 'w', encoding='utf-8', newline='\n')
    for i in range(N):
        rows = decode_glyph(rom, i)
        g = np.zeros((16, 16), np.float32)
        for r in range(14):
            for x in range(16):
                g[r, x] = 1 if rows[r] & (0x8000 >> x) else 0
        if g.sum() == 0:
            out.write('%d\t%04X\t \t1.0\t\n' % (i, i + 0x11))
            continue
        best = None
        for dy in (-1, 0, 1, 2):
            for dx in (-1, 0, 1):
                s = blur(np.roll(np.roll(g, dy, 0), dx, 1))
                s = s - s.mean()
                s /= np.sqrt((s * s).sum()) + 1e-6
                score = (R * s).sum(axis=(1, 2))  # normalised cross-correlation
                if best is None:
                    best = score
                else:
                    best = np.maximum(best, score)
        order = np.argsort(-best)
        top = []
        for k in order:
            if names[k] not in [t[0] for t in top]:
                top.append((names[k], best[k]))
            if len(top) == 3:
                break
        out.write('%d\t%04X\t%s\t%.3f\t%s\n' % (i, i + 0x11, top[0][0], top[0][1],
                                                 ' '.join('%s:%.3f' % t for t in top[1:])))
    out.close()


if __name__ == '__main__':
    main()
