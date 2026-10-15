-- Warp to a scene (script block) from a cold boot: the route below picks New Game, then the first stage load
-- (81:8EF1 LDA $0834) is redirected to block SCENE (0-59 = index into the block table at ROM 0xBE16).
--   emu.py ROM --out DIR --script tools/debug/warp.lua --var SCENE=12 --frames 3000 --mash 30 --sheet
--   emu.py ROM --out DIR --script tools/debug/warp.lua --var "SCENE='town1'" ...   (names: SCENES below)
-- Pass no --route; give --frames. Extra: --var "THEN='a;30 -;6 b'" is not supported; use --mash.
-- The scene list (name -> block, what is there) lives here so the warp needs no file lookup.
local mem = emu.memType.snesMemory
-- Every block 0-59 is reachable by number (tools/debug/regen.py shoots all of them: work/qa/scenes/).
-- Kakeru side ~0-29, Eto side ~30-57 (table order), 58 = ending + staff roll (reach staff roll with long --mash).
SCENES = {
  prologue = 0, town1 = 1, beach = 15, ship = 8, ending = 58, staff = 58,
}
local target = SCENE
if type(target) == "string" then target = assert(SCENES[target], "unknown scene " .. target) end
assert(type(target) == "number", "set --var SCENE=<block index or name>")
local done = false
L.on_exec(0x818EF1, 0x818EF1, function()
  if done then return end
  done = true
  emu.write(0x7E0834, target, mem)
  L.log(string.format("warp: scene %d at frame %d", target, L.frame))
end)
-- MODE: optional module switch some frames after the scene loaded ($A2 = module, $B6 = 0):
--   --var "MODE='battle'"  -> $A2=$09 (84:800F battle on the scene's map $0C00; deployment screen first)
--   --var "MODE='menu'"    -> $A2=$12 (81:D5AB field menu: items / status / load / options)
--   --var "MODE='epilogue'"-> $A2=$15 (86:8000 ending epilogue)
local MODES = { battle = 0x09, menu = 0x12, epilogue = 0x15, story = 0x0C }
if MODE then
  local m = assert(MODES[MODE], "unknown MODE " .. tostring(MODE))
  L.on_frame(function(f)
    if done and not modeDone and f >= (MODE_AT or 2300) then
      modeDone = true
      emu.write(0x7E00A2, m, mem)
      emu.write(0x7E00B6, 0, mem)
      L.log(string.format("mode %s at frame %d", MODE, f))
    end
  end)
end
-- title -> New Game
for _, s in ipairs({{1500, "-"}, {6, "start"}, {200, "-"}, {6, "start"}, {300, "-"}, {6, "a"}, {60, "-"}}) do
  L.press(s[2], s[1])
end
