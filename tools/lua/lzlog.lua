-- Log LZ decompressions (80:CE0E: src [$45-$47], dest $48 in bank $4A) with the caller's return address.
local mem = emu.memType.snesMemory
L.on_exec(0x80CE0E, 0x80CE0E, function()
  local s = emu.getState()
  local src = emu.read(0x45, mem) | emu.read(0x46, mem) << 8 | emu.read(0x47, mem) << 16
  local dst = emu.read(0x48, mem) | emu.read(0x49, mem) << 8 | emu.read(0x4A, mem) << 16
  local sp = s["cpu.sp"]
  local ret = emu.read(sp + 1, mem) | emu.read(sp + 2, mem) << 8 | emu.read(sp + 3, mem) << 16
  L.log(string.format("f%d lz src=%06X dst=%06X ret=%06X", L.frame, src, dst, ret))
end)
