-- Log battle glyph-pool string loads (84:93EF reads [$00],y with $00-$02 = pool table entry).
local mem = emu.memType.snesMemory
L.on_exec(0x8493EF, 0x8493EF, function()
  local p = emu.read(0, mem) | emu.read(1, mem) << 8 | emu.read(2, mem) << 16
  local a = emu.read(p, mem) | emu.read(p + 1, mem) << 8
  local b = emu.read(p + 2, mem) | emu.read(p + 3, mem) << 8
  L.log(string.format("f%d entry=%06X start=%04X end=%04X", L.frame, p, a, b))
end)
