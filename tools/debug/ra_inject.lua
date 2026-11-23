-- Reach a player's RetroArch Mesen-S state (MesenCE cannot load it): warp.lua START= to the same block and text,
-- then write the state's WRAM (raw 128 KB at state file offset 0xA5, saved as WRAM_FILE) at frame INJECT_AT.
-- RANGES = WRAM offsets to copy; skip direct page/stack and the text context, or the CPU hangs:
--   --var "RANGES={{0x0200,0x06FF},{0x0740,0x1DFF},{0x2000,0xFFFF}}"   (party roster lives in 7E:0200-1DFF)
-- Optional: A every PRESS_EVERY frames after the inject until PRESS_UNTIL. VRAM is not copied (map tiles garble).
local mem = emu.memType.snesMemory
local data = L.read_file(WRAM_FILE)   -- absolute path: the Lua cwd is the emulator's
L.on_frame(function()
  if L.frame > INJECT_AT and (L.frame - INJECT_AT) % (PRESS_EVERY or 90) == 0 and L.frame < (PRESS_UNTIL or 1e9) then
    L.press("a", 8)
  end
  if L.frame ~= INJECT_AT then return end
  for _, r in ipairs(RANGES or { { 0, #data - 1 } }) do
    for i = r[1], r[2] do emu.write(0x7E0000 + i, data:byte(i + 1), mem) end
  end
  L.log(string.format("injected at frame %d", L.frame))
end)
