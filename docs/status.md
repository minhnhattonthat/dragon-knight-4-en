# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 9 done. Last build: b22c7b0 Release v1.0 (local) (2026-10-21).
- **Done:** recon, debug warp (tools/debug/warp.lua, regen.py), extract (script/*.json, 85 batches in work/tl),
  engine (asm/dk4.asm: far calls + VWF), 12103/12103 units translated + reviewed, UI (ui/ui.json) seen in-game,
  graphics (docs/re/graphics.md), QA tours, release/dragon-knight-4_en.zip (Dragon_Knight_4_EN_v1.0.bps, patch SHA-1
  9792210694820442e865bdeb6f760d546d05645d, patched CRC32 BFB1E659). Repo restructured to fan-translation-template.
- **2026-10-22 agent playtest** (4 playtesters, docs/playtester-brief.md: prologue, Sonia, Limerin/throne room):
  fixed Options submenus (Slow/Normal/Fast, Stereo/Mono; relocated via ui.json ptr_refs/bank_refs), overflow pages
  of a named speaker now break at sentence ends when that costs no page (layout.pages_of), "{Name}" in English =
  mid-unit speaker tag (2F8000_1C44 Lydia & Hardis), glossary/style: Dark Realm, ?! not !?, Heh heh heh, wording.
  Release zip is now stale (v1.0 predates these fixes).
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
- **Next:** rebuild the release after the user's OK. Never publish.
- **Open bugs:** Title copyright lines ©エルフ / ©バンプレ企画 still Japanese
  (docs/re/graphics.md row: packed tile format, not yet decoded). Field Status list in warp states shows "Pierre" x5 + garbage (warp artifact? recheck on
  a real save). Region 2C0000_0BC1 (lone 。, 1 byte) stays Japanese.
- **Waiting on the user:** playtest feedback.
