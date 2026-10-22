-- Show any bank-85 battle-text stream: --var PTR=0xD8DD [--var NUM=2] (PTR = 85:xxxx, stream id offset + base + 2;
-- NUM = the number op 31 draws, $074F). Needs a battle-map state where the turn-end check runs, e.g.
-- work/playtest/states/bat23.mss with --mash 40 (text starts ~f3245): its battle-text branch is forced once.
local M = emu.memType.snesMemory
local forced = false
L.on_exec(0x84A390, 0x84A390, function()
  if not forced then forced = true; emu.write(0x000835, 1, M) end
end)
L.on_exec(0x84D81D, 0x84D81D, function()
  L.log(string.format("f%d D81D %02X%02X", L.frame, emu.read(0x000001, M), emu.read(0x000000, M)))
  if PTR then
    emu.write(0x000000, PTR & 0xFF, M)
    emu.write(0x000001, PTR >> 8, M)
    emu.write(0x000002, 0x85, M)
    emu.write(0x00074F, NUM or 2, M)
  end
end)
