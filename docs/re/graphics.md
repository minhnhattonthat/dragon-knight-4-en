# Graphics text survey

Japanese drawn as tiles (not through the font routines). Font-drawn UI is in ui/ui.json (tools/ui.py).

| Screen | State / route | Layer | Source | Status |
|---|---|---|---|---|
| Title logo, "New Game"/"Continue" | cold boot (tools/routes/boot.txt) | BG | already English in the original | no change |
| "Player Phase" banner | work/states/en_battle23.mss | OBJ | already English | no change |
| Battle command buttons 待機/攻撃/治療/破壊 (+YES/NO) | en_battle23, select a unit | OBJ 4bpp raw at 0x4DABC | redrawn by tools/gfx_buttons.py: Wait / Attack / Heal / Break | English, checked zoomed |
| Battle popups "SAVE しますか?", "終了しますか?", "降伏しますか?", "SAVE しました。" | en_battle23, cursor to the panel SAVE button, A | BG1 lo-res 4bpp; tiles LZ at C0:BE65 (+0x20 palette header), tilemaps 16x8 at 0x2A8C5 + 0x100*k | tools/gfx_popups.py: "Save the game?", "End this turn?", "Yield?", "Game saved." (block moved to $E0:E000; 128-tile limit forces the short "Yield?") | English, Save/Saved checked in-game, End/Yield in the preview render |
| Staff roll | scene 58, long mash | | already English (credits) | see work/qa/ending |

Not reached by the tools: the combat animation screen (needs a unit in attack range; the End-turn panel button did not respond to the scripted cursor). The runtime draw scan (tools/jpdraw.py) saw no Japanese glyphs from any font routine in the routes run.
