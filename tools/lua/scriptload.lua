-- Log each script block load (819616 copies [len16][data] from ROM [$00] to 7F0000).
local mem = emu.memType.snesMemory
L.on_exec(0x819616, 0x819616, function()
  local s = emu.getState()
  local d = s["cpu.d"]
  local p = emu.read(d, mem) | emu.read(d + 1, mem) << 8 | emu.read(d + 2, mem) << 16
  local sp = s["cpu.sp"]
  local r = {}
  for i = 1, 6 do r[#r + 1] = string.format("%02X", emu.read(sp + i, mem)) end
  L.log(string.format("f%d load %06X off=%06X len=%04X stk=%s", L.frame, p, L.rom_off(p),
    emu.read(p, mem) | emu.read(p + 1, mem) << 8, table.concat(r, " ")))
end)
