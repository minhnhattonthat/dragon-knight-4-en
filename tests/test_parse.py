import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tools'))
from dk4 import ROM_PATH, load_rom, load_glyphs, blocks  # noqa: E402
from vm import parse_block  # noqa: E402

pytestmark = pytest.mark.skipif(not os.path.exists(ROM_PATH), reason='original ROM not present')


def test_glyph_table_unique():
    g = load_glyphs()
    assert len(set(g.values())) == len(g)


def test_all_blocks_parse_and_targets_on_boundaries():
    rom, g = load_rom(), load_glyphs()
    for blk in blocks(rom):
        start, end, ops = parse_block(rom, g, blk)
        assert ops, blk
        # every op roundtrips byte-exact and ops tile [start, end) with no gaps
        body = rom[blk[2] + 2:blk[2] + 2 + end]
        pos = start
        for o in ops:
            assert o['off'] == pos
            assert body[pos:pos + len(o['raw'])] == o['raw']
            pos += len(o['raw'])
        assert pos == end
        # jump targets land on an op boundary or inside a text run (page start), never inside a command
        cmd_inside = set()
        for o in ops:
            if o['kind'] == 'cmd':
                cmd_inside.update(range(o['off'] + 1, o['off'] + len(o['raw'])))
        for o in ops:
            for t in o.get('targets', []):
                assert t not in cmd_inside, (blk[0], hex(o['off']), hex(t))
