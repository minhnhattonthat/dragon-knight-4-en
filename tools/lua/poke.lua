-- Poke WRAM at frame POKE_AT: --var POKE_AT=60 --var "POKES='0x7E00BB=0x80,0x7E0700=0x82'" (OR-ed into the byte)
-- Also logs every change of $B6 (game state) and $0C00/$0C0D.
local mem = emu.memType.snesMemory
local last = {}
L.on_frame(function(f)
  if f == (POKE_AT or 60) and POKES then
    for a, v in POKES:gmatch("(0x%x+)=(0x%x+)") do
      a, v = tonumber(a), tonumber(v)
      if SET then emu.write(a, v, mem) else emu.write(a, emu.read(a, mem) | v, mem) end
      L.log(string.format("f%d poke %06X %s %02X", f, a, SET and "=" or "|=", v))
    end
  end
  for _, a in ipairs({0x7E00B6, 0x7E0C00, 0x7E0C0D, 0x7E0837}) do
    local v = emu.read(a, mem)
    if last[a] ~= v then L.log(string.format("f%d %06X = %02X", f, a, v)); last[a] = v end
  end
end)
