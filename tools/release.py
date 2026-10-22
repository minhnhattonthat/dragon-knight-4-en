"""Release gate + package: tests -> build -> smoke -> runtime JP scan (tour logs) -> SNES checksum -> BPS make/apply
verify -> README -> release/dragon-knight-4_en.zip (patch + README). Never publishes anything.

python -X utf8 tools/release.py [--no-tour]   (--no-tour skips the jpdraw check of work/qa/tour logs)
jp_left.py is not a gate here: every byte 0x12-0xFF is a glyph code, so a byte scan flags all ROM data. The build's
region classifier (stats 'japanese', tests/test_build.py) and the runtime draw scan (tools/jpdraw.py) replace it.
"""
import hashlib
import os
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = Path(os.environ.get('SKILL', Path.home() / '.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game'))
ROM = ROOT / 'rom' / 'Dragon Knight 4 (Japan).sfc'
VERSION = '1.0'
SLUG = 'dragon-knight-4'
PATCH = 'Dragon_Knight_4_EN_v%s.bps' % VERSION
PY = [sys.executable, '-X', 'utf8']


def run(cmd, what):
    print('==', what, flush=True)
    r = subprocess.call([str(c) for c in cmd], cwd=ROOT)
    if r:
        sys.exit('release gate failed at: %s (exit %d)' % (what, r))


def hashes(b):
    return '%08X' % zlib.crc32(b), hashlib.md5(b).hexdigest(), hashlib.sha1(b).hexdigest()


def main():
    run(PY + ['-m', 'pytest', '-q', 'tests'], 'tests')
    run(PY + ['build.py', 'build'], 'build')
    built = ROOT / 'build' / 'dk4_en.sfc'
    run(PY + [SKILL / 'scripts' / 'emu.py', built, '--out', 'work/qa/release_smoke', '--route', 'tools/routes/boot.txt',
              '--smoke'], 'smoke')
    if '--no-tour' not in sys.argv:
        run(PY + ['tools/jpdraw.py', 'work/qa/tour'], 'runtime Japanese draw scan (work/qa/tour)')
    rel = ROOT / 'release'
    rel.mkdir(exist_ok=True)
    final = ROOT / 'work' / 'dk4_en_release.sfc'
    run(PY + [SKILL / 'scripts' / 'bps.py', 'snes-checksum', built, '--out', final], 'snes checksum')
    patch = rel / PATCH
    run(PY + [SKILL / 'scripts' / 'bps.py', 'make', ROM, final, patch], 'bps make')
    check = ROOT / 'work' / 'reapplied.sfc'
    run(PY + [SKILL / 'scripts' / 'bps.py', 'apply', ROM, patch, check], 'bps apply')
    if check.read_bytes() != final.read_bytes():
        sys.exit('re-applied patch differs from the build')
    o, b = ROM.read_bytes(), final.read_bytes()
    oc, om, os_ = hashes(o)
    bc, bm, bs = hashes(b)
    readme = (ROOT / 'docs' / 'README.release.txt').read_text(encoding='utf-8').format(
        version=VERSION, patch=PATCH, ocrc=oc, omd5=om, osha=os_, bcrc=bc, bsha=bs, size=len(o), psize=len(b))
    (rel / 'README.txt').write_text(readme, encoding='utf-8', newline='\r\n')
    z = rel / ('%s_en.zip' % SLUG)
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(patch, PATCH)
        zf.write(rel / 'README.txt', 'README.txt')
    p = patch.read_bytes()
    print('release:', z)
    print('patch %s  sha1 %s' % (PATCH, hashlib.sha1(p).hexdigest()))
    print('patched ROM crc32 %s sha1 %s' % (bc, bs))
    return 0


if __name__ == '__main__':
    sys.exit(main())
