-- Log dynamic UI string loads: 81:F626 / 84:93EF read [$00],y where $00-$02 = string-table entry (start, end words).
local mem = emu.memType.snesMemory
local seen = {}
local function hook(tag)
  return function()
    local p = emu.read(0, mem) | emu.read(1, mem) << 8 | emu.read(2, mem) << 16
    if seen[p] then return end
    seen[p] = true
    local a = emu.read(p, mem) | emu.read(p + 1, mem) << 8
    local b = emu.read(p + 2, mem) | emu.read(p + 3, mem) << 8
    L.log(string.format("f%d %s entry=%06X start=%04X end=%04X", L.frame, tag, p, a, b))
  end
end
L.on_exec(0x81F626, 0x81F626, hook("81"))
L.on_exec(0x8493EF, 0x8493EF, hook("84"))
