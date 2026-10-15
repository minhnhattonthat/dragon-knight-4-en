-- Runtime leftover-Japanese scan: log each distinct glyph code drawn by the dialogue (80:AEAE) and menu (80:B1B0)
-- glyph routines, with the English-mode flag and caller. tools/jpdraw.py classifies the codes with tbl/glyphs_jp.txt.
local mem = emu.memType.snesMemory
local seen = {}
local function hit(tag, code, en)
  local s = emu.getState()
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 1, mem) | emu.read(sp + 2, mem) << 8 | emu.read(sp + 3, mem) << 16
  local key = string.format("%s %04X %d %06X", tag, code, en, ret)
  if seen[key] then return end
  seen[key] = true
  L.log(string.format("DRAW %s f%d", key, L.frame))
end
L.on_exec(0x80AEAE, 0x80AEAE, function()
  local s = emu.getState()
  hit("dlg", s["cpu.a"] & 0xFFFF, emu.read(0x7E1E00, mem))
end)
L.on_exec(0x80B1B0, 0x80B1B0, function()
  local s = emu.getState()
  hit("menu", s["cpu.a"] & 0xFFFF, 0)
end)
