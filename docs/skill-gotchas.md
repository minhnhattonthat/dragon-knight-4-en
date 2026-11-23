# Skill gotchas (one line each: reference file, then the fact)

- references/emulator-qa.md: a RetroArch Mesen-S core state (`.stateN`, "RASTATE" + "MSS") is uncompressed; s9x_state.py does not read it. WRAM sat at file offset 0xA5 (found by searching the state for a script block the game copies to 7F:0000); the text VM context in WRAM then names the exact script offset on screen.
- references/emulator-qa.md: to play on from such a state, warp to the same script text, then write its WRAM into the running game minus direct page, stack and the VM context (all of WRAM hangs the CPU); game state follows, VRAM does not (tools/debug/ra_inject.lua).
