# Skill gotchas (one line each: reference file, then the fact)

- references/emulator-qa.md: a RetroArch Mesen-S core state (`.stateN`, "RASTATE" + "MSS") is uncompressed; s9x_state.py does not read it. WRAM sat at file offset 0xA5 (found by searching the state for a script block the game copies to 7F:0000); the text VM context in WRAM then names the exact script offset on screen.
