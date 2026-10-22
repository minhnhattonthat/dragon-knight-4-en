# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| [text.md](text.md) | font, script blocks, text VM, dictionary, jumps | verified (identity build, in-game) |
| [hooks.md](hooks.md) | asm/dk4.asm hook sites, new banks, WRAM use | verified (in-game) |
| [graphics.md](graphics.md) | graphics text survey, buttons, battle popups | verified; battle animation screen not reached |
