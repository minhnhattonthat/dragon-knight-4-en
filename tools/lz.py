"""DK4 LZ codec (decompressor 80:CE0E).

Stream: word W (little-endian).
  W & 0x8000 and W != 0x8000: stored block of (0x10000 - W) raw bytes.
  else: W = output size (0x8000 means 0x8000); then groups: flag byte, 8 bits MSB first;
        0 = literal byte; 1 = two bytes b1 b2: count = (b1 >> 3) + 2, offset = -(0x800 - ((b1 & 7) << 8 | b2))
        i.e. src = dst + (0xF800 | (b1 & 7) << 8 | b2) - 0x10000.
"""


def decompress(data, pos=0):
    """Returns (bytes, consumed)."""
    start = pos
    w = data[pos] | data[pos + 1] << 8
    pos += 2
    if w & 0x8000 and w != 0x8000:
        n = 0x10000 - w
        return bytes(data[pos:pos + n]), pos + n - start
    size = w
    out = bytearray()
    while len(out) < size:
        flags = data[pos]
        pos += 1
        for bit in range(8):
            if len(out) >= size:
                break
            if flags & (0x80 >> bit):
                b1, b2 = data[pos], data[pos + 1]
                pos += 2
                off = (0xF800 | (b1 & 7) << 8 | b2) - 0x10000
                cnt = (b1 >> 3) + 2
                src = len(out) + off
                for k in range(cnt):
                    out.append(out[src + k])
            else:
                out.append(data[pos])
                pos += 1
    return bytes(out[:size]), pos - start


def compress(raw):
    """Greedy LZ (window 2048, length 2..33)."""
    out = bytearray(len(raw).to_bytes(2, 'little'))
    i, n = 0, len(raw)
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if i >= n:
                break
            best_len, best_off = 0, 0
            lo = max(0, i - 2048)
            for j in range(lo, i):
                l = 0
                while l < 33 and i + l < n and raw[j + l] == raw[i + l]:
                    l += 1
                if l > best_len:
                    best_len, best_off = l, i - j
                    if l == 33:
                        break
            if best_len >= 3 or (best_len == 2):
                v = 0x10000 - best_off - 0xF800   # 0..0x7FF
                out += bytes([((best_len - 2) << 3) | (v >> 8), v & 0xFF])
                flags |= 0x80 >> bit
                i += best_len
            else:
                out.append(raw[i])
                i += 1
        out[flag_pos] = flags
    return bytes(out)


if __name__ == '__main__':
    import sys
    sys.path.insert(0, __file__.rsplit('\\', 1)[0])
    from dk4 import load_rom, lorom
    rom = load_rom()
    for a in (0xBFBAE6, 0xBFA242, 0xBF9FC3, 0x9A836F):
        raw, used = decompress(rom, lorom(a))
        c = compress(raw)
        assert decompress(c)[0] == raw
        print(hex(a), len(raw), used, len(c))
