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
-- title -> New Game
for _, s in ipairs({{1500, "-"}, {6, "start"}, {200, "-"}, {6, "start"}, {300, "-"}, {6, "a"}, {60, "-"}}) do
  L.press(s[2], s[1])
end
