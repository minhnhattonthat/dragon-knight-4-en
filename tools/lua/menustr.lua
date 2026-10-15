-- Log menu string draws: 81:F0B5 draws the string at [$00] (codes as in the script, 00-terminated) via 80:B160.
local mem = emu.memType.snesMemory
local seen = {}
L.on_exec(0x81F0B5, 0x81F0B5, function()
  local s = emu.getState()
  local p = emu.read(0, mem) | emu.read(1, mem) << 8 | emu.read(2, mem) << 16
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 1, mem) | emu.read(sp + 2, mem) << 8 | emu.read(sp + 3, mem) << 16
  local key = string.format("%06X", p)
  if seen[key] then return end
  seen[key] = true
  local t = {}
  for i = 0, 40 do t[#t + 1] = string.format("%02X", emu.read(p + i, mem)) end
  L.log(string.format("f%d str=%06X ret=%06X %s", L.frame, p, ret, table.concat(t, " ")))
end)
