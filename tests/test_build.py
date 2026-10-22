"""Builds its own ROM (no stale build/ artifact) and checks: layout errors, leftover Japanese in en, romdiff ranges."""
import glob
import json
import os
import re
import subprocess
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from dk4 import ROM_PATH  # noqa: E402

pytestmark = pytest.mark.skipif(not os.path.exists(ROM_PATH), reason='original ROM not present')
SKILL = os.environ.get('SKILL', os.path.expanduser('~/.claude/plugins/marketplaces/retro-translation/skills/translate-retro-game'))
ROMDIFF = os.path.join(SKILL, 'scripts', 'romdiff.py')
JP = re.compile('[\u3040-\u30ff\u4e00-\u9fff]')


@pytest.fixture(scope='module')
def built(tmp_path_factory):
    import build
    img, stats, errors = build.build('build')
    path = str(tmp_path_factory.mktemp('b') / 'dk4_en.sfc')
    open(path, 'wb').write(img)
    build.assemble(path)
    return path, stats, errors


def test_no_layout_errors(built):
    _, stats, errors = built
    assert errors == [] and stats['errors'] == 0
    assert stats['japanese'] <= 1   # region 2C0000_0BC1: a lone 1-byte 。, kept


def test_english_has_no_japanese():
    bad = []
    for f in glob.glob(os.path.join(ROOT, 'script', '*.json')):
        for e in json.load(open(f, encoding='utf8')):
            if e.get('en') and JP.search(e['en']):
                bad.append(e['id'])
    assert not bad, bad[:20]


def test_romdiff_allowed_ranges(built):
    ranges = [ln.split()[0] for ln in open(os.path.join(ROOT, 'tools', 'allowed_ranges.txt'))
              if ln.strip() and not ln.startswith('#')]
    r = subprocess.run([sys.executable, '-X', 'utf8', ROMDIFF, ROM_PATH, built[0]] + ranges,
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout[-2000:] + r.stderr[-500:]
