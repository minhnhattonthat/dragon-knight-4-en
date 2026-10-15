"""Sampled page tour: start each scene's script at a few dialogue pages (warp.lua START) and mash through, so town
NPC text is seen without walking. Writes work/qa/pages/sNN_OOOO/ (shots + log) and a cropped text-box sheet each.

python -X utf8 tools/debug/pagetour.py ROM [--per 3] [--frames 3600] [--jobs 3] [--scenes 0,1]
Then: python -X utf8 tools/jpdraw.py work/qa/pages
"""
import argparse
import glob
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SK = r'H:\translation\batch\.claude\skills\translate-retro-game\scripts'


def starts(per):
    out = []
    for f in sorted(glob.glob(os.path.join(ROOT, 'script', 'b*.json'))):
        sc = int(os.path.basename(f)[1:3])
        if sc >= 60:
            continue   # epilogue stream: reached with MODE='epilogue'
        offs = sorted({int(e['id'].split('_')[1].split('.')[0], 16) for e in json.load(open(f, encoding='utf-8'))
                       if e.get('form') == 'dlg' and e.get('en')})
        for k in range(per):
            if offs:
                out.append((sc, offs[(len(offs) * (2 * k + 1)) // (2 * per)]))
    return out


def run(rom, sc, off, frames, out):
    d = os.path.join(out, 's%02d_%04X' % (sc, off))
    cmd = [sys.executable, '-X', 'utf8', os.path.join(SK, 'emu.py'), rom, '--out', d,
           '--sav', os.path.join(ROOT, 'work', 'states', 'blank.srm'),
           '--script', os.path.join(ROOT, 'tools', 'debug', 'warp.lua'), '--var', 'SCENE=%d' % sc,
           '--var', 'START=0x%04X' % off, '--frames', str(frames), '--mash', '60', '--shot-every', '60',
           '--script', os.path.join(ROOT, 'tools', 'lua', 'jpdraw.lua')]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(SK, 'sheet.py'), d, '--changed', '0.005', '--from', '2000',
                    '--crop', '0,320,512,128', '--div', '2', '--max', '24', '--out', d + '.png'], capture_output=True)
    return sc, off, r.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom')
    ap.add_argument('--per', type=int, default=3)
    ap.add_argument('--frames', type=int, default=3600)
    ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--scenes')
    ap.add_argument('--out', default=os.path.join(ROOT, 'work', 'qa', 'pages'))
    a = ap.parse_args()
    todo = starts(a.per)
    if a.scenes:
        keep = {int(s) for s in a.scenes.split(',')}
        todo = [t for t in todo if t[0] in keep]
    bad = 0
    with ThreadPoolExecutor(a.jobs) as ex:
        for sc, off, rc in ex.map(lambda t: run(os.path.abspath(a.rom), t[0], t[1], a.frames, a.out), todo):
            print('s%02d_%04X rc=%d' % (sc, off, rc), flush=True)
            bad += rc != 0
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
