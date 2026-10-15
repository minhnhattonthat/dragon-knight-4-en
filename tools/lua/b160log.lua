-- Log calls to the menu string renderer 80:B160 (A = code or dictionary code, Y = cell buffer) with caller.
local mem = emu.memType.snesMemory
local seen = {}
L.on_exec(0x80B160, 0x80B160, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 1, mem) | emu.read(sp + 2, mem) << 8 | emu.read(sp + 3, mem) << 16
  local key = string.format("%04X@%06X", s["cpu.a"], ret)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("f%d B160 A=%04X Y=%04X ret=%06X", L.frame, s["cpu.a"], s["cpu.y"], ret))
end)
L.on_exec(0x80AEAE, 0x80AEAE, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 1, mem) | emu.read(sp + 2, mem) << 8
  if ret ~= 0xB2E1 then
    local key = string.format("G%04X@%04X", s["cpu.a"], ret)
    if seen[key] then return end
    seen[key] = true
    L.log(string.format("f%d AEAE A=%04X ret=%04X", L.frame, s["cpu.a"], ret))
  end
end)
