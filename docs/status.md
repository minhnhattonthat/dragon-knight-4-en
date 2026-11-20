# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 done. Last build: b22c7b0 Release v1.0 (local) (2026-10-21).
- **Done:** recon, debug warp (tools/debug/warp.lua, regen.py), extract (script/*.json, 85 batches in work/tl),
  engine (asm/dk4.asm: far calls + VWF), 12103/12103 units translated + reviewed, UI (ui/ui.json) seen in-game,
  graphics (docs/re/graphics.md), QA tours, release/dragon-knight-4_en.zip (v1.1, 2026-10-22 from c9d35d5:
  Dragon_Knight_4_EN_v1.1.bps, patch SHA-1 b7564a7ef318a44d2ef728ff19b0d9dec511efe7, patched CRC32 27F76018). Published 2026-10-22: github.com/minhnhattonthat/dragon-knight-4-en, release v1.1
  (remote is HTTPS: the local SSH key is another account; push with gh's credential helper). Repo restructured to fan-translation-template.
- **2026-11-20 template sync:** .codex/.opencode agent types, docs/{graphics,story-reviewer,visual-qa}-brief.md,
  docs/screenshots/, tools/skill.py (skill path), tools/{bps,romdiff}.py local copies, tools/hooks/pre-commit
  (core.hooksPath), new clean.py (keeps QA records); local guard hook dropped (plugin ships it).
  No work/qa/**/manifest.tsv exists now: the plugin guard blocks `gh release create` until a QA tour + qa_gate run.
- **2026-10-22 agent playtest** (4 playtesters, docs/playtester-brief.md: prologue, Sonia, Limerin/throne room):
  fixed Options submenus (Slow/Normal/Fast, Stereo/Mono; relocated via ui.json ptr_refs/bank_refs), overflow pages
  of a named speaker now break at sentence ends when that costs no page (layout.pages_of), "{Name}" in English =
  mid-unit speaker tag (2F8000_1C44 Lydia & Hardis), glossary/style: Dark Realm, ?! not !?, Heh heh heh, wording.
  In the rebuilt zip.
- **2026-10-22 battle / town playtest:** fixed enemy names on the map panel (ui.py skipped `en_tsv` entries, so
  tbl_names was never written), combat screen name plates (tools/gfx_plates.py + asm plate_font/plate_ptrs:
  precomposed proportional names, up to 64 px), garbled YES/NO popup on cursor move (button-row maps 0x2ACC5/0x2AD05
  re-tiled). Names from the half-width plate list: Menkiyou -> Menkyou, Wohhenrims -> Jochenrims (ヨッヘンリムス,
  glyph misread). Training ground hire, notebook save: OK. The game has no shops or inns.
- **2026-10-22 battle event text:** bank 85 streams = regions.py blocks 61-67 (script/b61..b67, 491 unique units,
  batches b087-b090), translated, reviewed (Important fixed, cheap Minors applied), merged. Powell's でござる =
  ", good sir" (decisions D7). Seed/stat lines: op 31 draws $074F inline; build carries the line/col
  across it (INLINE_OPS, layout attach/last_room), convention in docs/translator-brief.md. Seed tables per character:
  85:D44C power, DB40 defense, E245 speed, E985 range (caller 84:DF68..DFEF). In-game check: tools/debug/battletext.lua
  (--var PTR=0xD8DD NUM=2, state bat23.mss, --mash 40, then tools/debug/pages.py RUN 3200). Seen OK: Gina power, Mayfair speed, Pandora range.
- **2026-10-22 field menu Load (user report: black screen on load):** the field Load screen (81:E2E8, 81:E384)
  read the relocated place names with bank $85 (stale bytes, some with 10 xx ops, runs up to 71 bytes; Ulysses
  drew "長…") and drew the notebook names 81:E30E in Japanese. Fixed: notebook_places bank_refs 0xE2F1/0xE38D,
  ui.json notebooks_field. Save red + field Load + title Continue verified in Mesen (Ulysses). Fixed in v1.1.
- **2026-11-20 issue #3 (player report, screenshots only):** fixed Marian's House sign (talk script before the
  block's first header word, vm.parse_block now starts at the lowest header entry that parses), blank line after a
  name-only region (layout trailing nl), name tag pushed to the bottom line after a name + conditional jump (build
  carries the line into jump targets, through command-only chains: regions.next_targets; op 40 is a cond jump),
  Hardis "Huh?", save popup "game" (bold closed m's gaps: popups widen 1-px gaps), notebook choice "Red notebook"
  column (choice region pads to the JP trailing blanks, 40 menus). Verified by warp (+ $07F4 flag Lua) for Marian,
  Gant, Rank, Kakeru, notebook. Not reproduced: Linus "...iiiiife" (shot shows no blank line). Not checked in
  game: Charon battle quote, save popup (preview only). Backward jump targets (28, loops) still start at line 0.
  PR #4 follow-up: Linus 2FB86E_2470 "...iiiiiife" -> "Waaaaaaaah......" (player found it confusing); town-exit
  refusals 2F0269_1DA4/1E4C, 2F9C88_10C0 (reported blank line after 【Kakeru】, v1.1 shots) already fixed by the
  name-only trailing-nl fix: verified by warp (START=0x1D9B / 0x10B7, $07F4 cleared to fall through).
- **2026-11-20 v1.2 (issue #3 hotfix):** release/dragon-knight-4_en.zip from 719a6f7 + VERSION bump:
  Dragon_Knight_4_EN_v1.2.bps, patch SHA-1 98007d70d247554bda128ac70c19372212ad89b8, patched CRC32 6D8C1F3C
  (SHA-1 0b29bb00bb3891e5273588e46bd6619ef65e6c40). Tour work/qa/tour: 60 scenes rc=0, jpdraw 0 Japanese;
  work/qa/manifest.tsv has 360 sheets with no visual-QA verdicts (waiver recorded; the user publishes by hand).
- **Next:** player bug reports (`gh issue list --label bug`). Never publish without the user.
- **Open bugs:** Title copyright lines ©エルフ / ©バンプレ企画 still Japanese
  (docs/re/graphics.md row: packed tile format, not yet decoded). Field Status list in warp states shows "Pierre" x5 + garbage (warp artifact? recheck on
  a real save). Region 2C0000_0BC1 (lone 。, 1 byte) stays Japanese.
- **Waiting on the user:** playtest feedback.
