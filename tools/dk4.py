"""Dragon Knight 4 (SFC) script format: blocks, VM opcodes, text codec.

Script blocks: 60-entry table at ROM 0xBE16 (4 bytes: 24-bit LoROM ptr, scene byte); each block is
[len16][len bytes], copied to 7F:0000 by 81:9615 and run by the text VM at 80:B2B6.
VM stream bytes:
  00        end of message / wait (B2F9)
  01-0F xx  16-bit glyph code (hi, lo); >= 0x6CC would be a dictionary ref (85:D08E), unused
  10 op ..  command op (table 80:B359), ARGS[op] argument bytes
  11        line break (B30D)
  12-FF     glyph code
Glyph index = code - 0x11 (font at 0x40000, see font.py).
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ROM_PATH = os.path.join(ROOT, 'rom', 'Dragon Knight 4 (Japan).sfc')
BLOCK_TABLE = 0xBE16
BLOCK_COUNT = 60

# argument byte counts per command op (10 op ...)
ARGS = {
    0x00: 0, 0x01: 0, 0x02: 1, 0x03: 1, 0x04: 2, 0x05: 1, 0x06: 0, 0x07: 1, 0x08: 1, 0x09: 3, 0x0A: 4, 0x0B: 2,
    0x0C: 1, 0x0D: 4, 0x0E: 1, 0x0F: 3, 0x10: 0, 0x11: 0, 0x12: 2, 0x13: 0, 0x14: 2, 0x15: 0, 0x16: 0, 0x17: 2,
    0x18: 4, 0x19: 5, 0x1A: 2, 0x1B: 0, 0x1C: 4, 0x1D: 1, 0x1E: 1, 0x1F: 2, 0x20: 0, 0x21: 1, 0x22: 0, 0x23: 4,
    0x24: 3, 0x25: 2, 0x26: 2, 0x27: 1, 0x28: 1, 0x29: 2, 0x2A: 2, 0x2B: 4, 0x2C: 1, 0x2D: 3, 0x2E: 2, 0x2F: 2,
    0x30: 1, 0x31: 0, 0x32: 3, 0x33: 0, 0x34: 0, 0x35: 4, 0x36: 4, 0x37: 0, 0x38: 0, 0x39: 1, 0x3A: 0, 0x3B: 2,
    0x3C: 1, 0x3D: 2, 0x3E: 0, 0x3F: 1, 0x40: 4, 0x41: 4, 0x42: 2, 0x43: 0,
}
# op 0C (choice) layout byte -> option count (80:CA78); followed by count+1 jump targets (last = cancel)
CHOICE_N = [0, 0, 2, 3, 4, 5, 6, 4, 8]
# ops whose last two arg bytes are a 16-bit jump target (7F:xxxx = block offset)
JUMP_ARG = {0x0A: 2, 0x12: 0, 0x14: 0, 0x32: 1, 0x35: 2, 0x40: 2, 0x41: 2}


def lorom(addr):
    return ((addr & 0x7F0000) >> 1) | (addr & 0x7FFF)


def load_rom(path=ROM_PATH):
    return open(path, 'rb').read()


def load_glyphs(path=os.path.join(ROOT, 'tbl', 'glyphs_jp.txt')):
    """code -> char (one-to-one; alternates carry a '*')."""
    m = {}
    for ln in open(path, encoding='utf-8'):
        ln = ln.rstrip('\n')
        if ln.startswith('#') or not ln.strip():
            continue
        code, chars = ln.split(' ', 1)
        c = int(code, 16)
        cells = []
        for ch in chars:
            if ch == '*':
                cells[-1] += '*'
            else:
                cells.append(ch)
        for i, ch in enumerate(cells):
            if ch != '_':
                m[c + i] = ch
    rev = {}
    for k, v in m.items():
        assert v not in rev, 'duplicate glyph %s at %X and %X' % (v, rev[v], k)
        rev[v] = k
    return m


DICT_TABLE = 0x28ED0  # 85:8ED0, 16-bit ptrs into bank 85; code 0x6CC + i
DICT_FIRST = 0x6CC
DICT_COUNT = 359


def dict_entries(rom):
    """[(code, rom_off, raw bytes incl. 00 terminator)]"""
    out = []
    for i in range(DICT_COUNT):
        p = rom[DICT_TABLE + 2 * i] | rom[DICT_TABLE + 2 * i + 1] << 8
        a = lorom(0x850000 | p)
        e = a
        while rom[e] != 0:  # 00 terminates only at a code position (10 op arg may be 00)
            if rom[e] == 0x10:
                e += 2 + ARGS[rom[e + 1]]
            elif rom[e] < 0x10:
                e += 2
            else:
                e += 1
        out.append((DICT_FIRST + i, a, rom[a:e + 1]))
    return out


def blocks(rom):
    """[(table_index, scene, rom_off, length)] in table order (two table slots share some blocks)."""
    out = []
    for i in range(BLOCK_COUNT):
        o = BLOCK_TABLE + 4 * i
        p = rom[o] | rom[o + 1] << 8 | rom[o + 2] << 16
        off = lorom(p)
        out.append((i, rom[o + 3], off, rom[off] | rom[off + 1] << 8))
    return out
