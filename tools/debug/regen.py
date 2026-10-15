"""Warp to every scene from a cold boot, save a state + contact sheet per scene.

python -X utf8 tools/debug/regen.py ROM [--scenes 0,5,58] [--frames 3000] [--jobs 3] [--out work/qa/scenes]
States: work/states/scene_NN.mss (taken at the end of the run). Regenerate after engine/font/graphics changes.
"""
import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EMU = r'H:\translation\batch\.claude\skills\translate-retro-game\scripts\emu.py'


def run(rom, sc, frames, out, mash, extra=(), state=True):
    d = os.path.join(out, 'scene_%02d' % sc)
    cmd = [sys.executable, '-X', 'utf8', EMU, rom, '--out', d, '--script', os.path.join(ROOT, 'tools', 'debug', 'warp.lua'),
           '--var', 'SCENE=%d' % sc, '--frames', str(frames), '--mash', str(mash), '--shot-every', '200', '--sheet']
    if state:
        cmd += ['--state-out', os.path.join(ROOT, 'work', 'states', 'scene_%02d.mss' % sc)]
    for x in extra:
        cmd += ['--script', os.path.abspath(x)]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return sc, r.returncode, r.stdout.strip().splitlines()[-1:] if r.stdout else r.stderr[-300:]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('rom')
    ap.add_argument('--scenes', default=','.join(str(i) for i in range(60)))
    ap.add_argument('--frames', type=int, default=3000)
    ap.add_argument('--mash', type=int, default=30)
    ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--out', default=os.path.join(ROOT, 'work', 'qa', 'scenes'))
    ap.add_argument('--script', action='append', default=[], help='extra Lua hook (e.g. tools/lua/jpdraw.lua)')
    ap.add_argument('--no-state', action='store_true', help='tour only: do not overwrite work/states')
    a = ap.parse_args()
    os.makedirs(os.path.join(ROOT, 'work', 'states'), exist_ok=True)
    scenes = [int(s) for s in a.scenes.split(',')]
    bad = 0
    with ThreadPoolExecutor(a.jobs) as ex:
        for sc, rc, tail in ex.map(lambda s: run(os.path.abspath(a.rom), s, a.frames, a.out, a.mash, a.script, not a.no_state), scenes):
            print('scene %02d rc=%d %s' % (sc, rc, tail), flush=True)
            bad += rc != 0
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
