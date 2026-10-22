# Graphics text survey

Japanese drawn as tiles (not through the font routines). Font-drawn UI is in ui/ui.json (tools/ui.py).

| Screen | State / route | Layer | Source | Status |
|---|---|---|---|---|
| Title logo, "New Game"/"Continue" | cold boot (tools/routes/boot.txt) | BG | already English in the original | no change |
| Title copyright "©エルフ 1994 / ©バンプレ企画 1996" (third line ©BANPRESTO already English) | cold boot, frame 1520 | BG3 2bpp, chr $0000, map $1800; map rows raw at 81:8C27 (+0x22 per row, 17 words, DMA'd to $1A88/$1AA8/...); tiles = LZ at C4:870E (file 0x22070E, 0xA00 bytes) into 7F:0000, then 80:D2xx converts a packed pixel format to planar (32-byte units) before the DMA at f1489. tools/lz.py output diverges from the game's buffer at byte 0x4C0 (unexplained) | **Japanese**: needs the inverse of the 80:D2xx transform + recompression |
| "Player Phase" banner | work/states/en_battle23.mss | OBJ | already English | no change |
| Battle command buttons 待機/攻撃/治療/破壊 (+YES/NO) | en_battle23, select a unit | OBJ 4bpp raw at 0x4DABC | redrawn by tools/gfx_buttons.py: Wait / Attack / Heal / Break | English, checked zoomed |
| Battle popups "SAVE しますか?", "終了しますか?", "降伏しますか?", "SAVE しました。" | en_battle23, cursor to the panel SAVE button, A | BG1 lo-res 4bpp; tiles LZ at C0:BE65 (+0x20 palette header), tilemaps 16x8 at 0x2A8C5 + 0x100*k | tools/gfx_popups.py: "Save the game?", "End this turn?", "Yield?", "Game saved." (block moved to $E0:E000; 128-tile limit forces the short "Yield?") | English, Save/Saved checked in-game, End/Yield in the preview render |
| Staff roll | scene 58, long mash | | already English (credits) | see work/qa/ending |

| Battle popup YES/NO highlighted button rows (drawn when the cursor moves) | work/playtest/s_bat23/0050.mss, left/right | BG1, 16x2 maps at 0x2ACC5 / 0x2AD05 (descriptors 85:A8B7) | re-tiled with the popups by tools/gfx_popups.py (were garbage after the re-tile) | English, checked |
| Combat screen name plates (クラリス / カトロニア) | work/playtest/s_bat23/0010.mss, A | BG1 4bpp, font LZ 82:CCD3 (kana = tile code-$60+$100), names = packed half-width katakana 82:C6BB | precomposed proportional names, tools/gfx_plates.py + plate_font/plate_ptrs (docs/re/hooks.md) | English, checked (Clarice, Catronia, Necromancer, Oppenheimer) |

Combat screen reached from work/playtest/s_bat23/0010.mss (press A). The runtime draw scan (tools/jpdraw.py) saw no Japanese glyphs from any font routine in the routes run.
