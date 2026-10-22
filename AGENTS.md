# Dragon Knight 4 (SNES, Banpresto 1996) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = the directory holding its SKILL.md). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py build`        -> build/dk4_en.sfc (checks the dump against `rom.sha1` first; `build.py marker` = marker build)
- Check:    `python -X utf8 tools/check.py`  (tests + lint; the pre-commit hook runs this)
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/dk4_en.sfc --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/dk4_en.sfc --out work/qa/warp --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 900 --sheet` (scenes: `tools/debug/scenes.lua`; never ask the user to play to a scene)
- Release:  `python -X utf8 tools/release.py` (patch + verify; never publish without the user; `$SKILL` env var overrides the plugin path)
- Clean:    `python -X utf8 tools/clean.py` (published projects: lists rebuildable/downloadable files; `--yes` deletes)
- Tour:     `python -X utf8 tools/debug/regen.py build/dk4_en.sfc --frames 18000 --no-state --out work/qa/tour
  --script tools/lua/jpdraw.lua` then `python -X utf8 tools/jpdraw.py work/qa/tour`.
- Page tour: `python -X utf8 tools/debug/pagetour.py build/dk4_en.sfc --out work/qa/pages3` (warp.lua START = script
  offset; reaches town NPC text). The first 3 glyphs after a START jump are junk (artifact: the op before is skipped).

## Paths
- Original ROM: `rom/Dragon Knight 4 (Japan).sfc` (gitignored; CRC32 52FC7228; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`). Emulator: this repo's own copy in `tools/mesen/` (MesenCE 2.2.1, github.com/nesdev-org/MesenCE releases; gitignored; settings in `tools/emu-config/`). Savestates: `work/states/`.
- Text: `script/` (JSON per block). Glyph table: `tbl/glyphs_jp.txt`. UI text: `ui/ui.json` (tools/ui.py). Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.
- Format code: `tools/dk4.py` (constants), `tools/vm.py` (script VM parser), `tools/font.py` (16x14 1bpp font).

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Script blocks are patched IN PLACE (far-call tokens), so unknown pointers in headers/object tables stay valid. Never move bytes inside a block.
- ALWAYS pass `--sav work/states/blank.srm` to emu.py runs (a battle SAVE writes tools/mesen/Saves/dk4_en.srm and the
  title then shows the notebook menu). work/states/en_save.srm has data but gives no title Continue (JP ROM too).
- Agent playtests: `docs/playtester-brief.md`, ROM copied to `work/playtest/` first, states made on that ROM.
- Layout: MAX_PX=376 (last cell is under the box frame); mid-line continuations (build.midline_targets),
  conditional-jump line carry (FALLTHROUGH_OPS), page-edge padding when the JP region ends on a page edge.
- Allowed ROM write ranges: `tools/allowed_ranges.txt` (tests/test_build.py romdiff).

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
