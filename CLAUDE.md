# Dragon Knight 4 (SNES, Banpresto 1996) English translation

Skill: translate-retro-game (H:\translation\batch\.claude\skills\translate-retro-game\SKILL.md). Read it before ROM, text or QA work. `$SKILL` = that directory.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py build`        -> build/dk4_en.sfc (`build.py marker` = marker build)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/dk4_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/dk4_en.sfc --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (scenes: `tools/debug/scenes.lua`)
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish)

## Paths
- Original ROM: `rom/Dragon Knight 4 (Japan).sfc` (gitignored; CRC32 52FC7228, SHA-1 cfb5d2ce3eab576dae49f570284b75c1a8c0465d). Emulator: `tools/mesen/` (MesenCE 2.2.1, github.com/nesdev-org/MesenCE releases, gitignored). Savestates: `work/states/`.
- Text: `script/` (JSON per block). Glyph table: `tbl/glyphs_jp.txt`. Glossary + rulings: `glossary.md`. RE notes: `docs/re/README.md`.
- Format code: `tools/dk4.py` (constants), `tools/vm.py` (script VM parser), `tools/font.py` (16x14 1bpp font).

## Rulings (pre-approved by user)
- Full names/terms, no abbreviations; engine work before cutting. Honorifics dropped; given name first. Romanization: no official EN; Hepburn / obvious Western names. Credits in English. Graphics text in scope.
- Edit source files only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Script blocks are patched IN PLACE (far-call tokens), so unknown pointers in headers/object tables stay valid. Never move bytes inside a block.

## Status
- Done: Step 0, recon, debug warp (tools/debug/warp.lua, regen.py), extract (script/*.json, 85 batches in work/tl),
  engine (asm/dk4.asm: far calls + VWF), marker/stress builds verified in-game, pilot b000 merged.
- Phase 6 done: 12103/12103 units translated + reviewed (fix001/fix002 merged).
- UI (ui/ui.json via tools/ui.py) done + seen in-game: main menu, options, status, party list, battle panel,
  unit types, enemy names, command buttons, unit info box (op 21), item list/count/stat box, combat labels.
- Phase 7: tests/test_build.py (own build, layout, JP-in-en, romdiff vs tools/allowed_ranges.txt). Layout MAX_PX=376
  (last cell is under the box frame); stub-page check in batches.py; fix003-006 merged (0 stub pages).
- Graphics: docs/re/graphics.md (buttons, battle popups via tools/gfx_popups.py). Notebook place names: ui.json notebook_places.
- Phase 8: tour = `python -X utf8 tools/debug/regen.py build/dk4_en.sfc --frames 18000 --no-state --out work/qa/tour
  --script tools/lua/jpdraw.lua` then `python -X utf8 tools/jpdraw.py work/qa/tour`. ALWAYS pass `--sav work/states/blank.srm`
  to emu.py runs (a battle SAVE writes tools/mesen/Saves/dk4_en.srm and the title then shows the notebook menu).
  Battle SAVE route + popups: see work/qa notes in docs/re/graphics.md. work/states/en_save.srm = a real save.
- Next: phase 9 release (`python -X utf8 tools/release.py`).
- Open bugs: none known. Region 2C0000_0BC1 (lone 。, 1 byte) stays Japanese.
