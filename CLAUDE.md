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
- Done: Step 0, recon of text VM/font/dict. Next: debug tool, identity build, extract. Open bugs: none.
