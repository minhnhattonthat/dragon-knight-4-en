"""Classify tools/lua/jpdraw.lua logs: report Japanese glyphs the game really drew.

python -X utf8 tools/jpdraw.py work/qa/tour      (reads */log.txt; exit 1 if any kana/kanji was drawn)
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dk4 import load_glyphs  # noqa: E402

JP = re.compile('[぀-ヿ一-鿿]')


def main(root):
    g = load_glyphs()
    hits = {}
    for log in sorted(glob.glob(os.path.join(root, '*', 'log.txt'))):
        scene = os.path.basename(os.path.dirname(log))
        for ln in open(log, encoding='utf8', errors='replace'):
            if not ln.startswith('DRAW '):
                continue
            tag, code, en, ret, frame = ln.split()[1:6]
            code, en = int(code, 16), int(en)
            if (tag == 'dlg' and en and 0x20 <= code < 0x80) or 0xB00 <= code < 0xE00:
                continue   # English VWF letter / precomposed English cell
            ch = g.get(code, '').rstrip('*')
            if JP.search(ch):
                hits.setdefault((tag, ret), []).append((scene, frame, ch))
    for (tag, ret), xs in sorted(hits.items()):
        scenes = sorted({s for s, _, _ in xs})
        print('%s ret=%s %d glyphs %r scenes %s first %s %s' % (tag, ret, len(xs), ''.join(c for _, _, c in xs[:20]),
                                                                  ','.join(scenes[:8]), xs[0][0], xs[0][1]))
    print('%d callers drew Japanese' % len(hits))
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))
