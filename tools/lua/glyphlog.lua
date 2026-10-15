-- Log every glyph draw: char code (A) at the glyph routine 80AEAE, plus the return address on the stack.
local mem = emu.memType.snesMemory
L.on_exec(0x80AEAE, 0x80AEAE, function()
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local r = {}
  for i = 1, 9 do r[#r + 1] = string.format("%02X", emu.read(sp + i, mem)) end
  L.log(string.format("f%d A=%04X X=%04X Y=%04X DB=%02X D=%04X stk=%s", L.frame, s["cpu.a"], s["cpu.x"], s["cpu.y"],
    s["cpu.dbr"], s["cpu.d"], table.concat(r, " ")))
end)
