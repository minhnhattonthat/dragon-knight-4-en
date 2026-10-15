-- Log the text reader's pointer at 80B2C1 (LDA [$00],y): 24-bit base in DP $00-$02, offset Y.
local mem = emu.memType.snesMemory
local last = -1
L.on_exec(0x80B2C1, 0x80B2C1, function()
  local s = emu.getState()
  local d = s["cpu.d"]
  local base = emu.read(d, mem) | emu.read(d + 1, mem) << 8 | emu.read(d + 2, mem) << 16
  local p = base + s["cpu.y"]
  if p ~= last then
    L.log(string.format("f%d base=%06X y=%04X b=%02X", L.frame, base, s["cpu.y"], emu.read(p, mem)))
  end
  last = p + 1
end)
