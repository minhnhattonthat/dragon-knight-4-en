# Engine hooks (asm/dk4.asm, asar 1.91, applied by build.py after the data writes)

| Site | Original | Hook | Purpose |
|---|---|---|---|
| 80:B318 | `STY $30,x / SBC #$06CC` (dictionary call) | far_hook | codes 0x833-0xAFF: short far text call via FARSHORT ($E0:8000, 4 bytes: ptr24 + skip8); 0x0F b0 b1 b2 s0 s1: long far call (skip16); 0xEFF: far return; 0xB00-0xDFF: precomposed cell drawn as a glyph |
| 80:AEAE | glyph routine entry | vwf_hook | in far (English) text: compose one 16-px cell from ASCII letters (VWF with carry into the next cell; 0x7F flushes the carry); precomposed cells from $E1:8000 |
| 80:B169 | menu renderer `CMP #$06CC` | b160_hook | precomposed codes take the single-glyph path |
| 80:B1B0 | menu glyph draw | b1b0_hook | precomposed codes read their cell from $E1:8000 |
| 80:C3F0 | op 21 unit-info printer `CMP #$06CC` | c3f0_hook | precomposed codes are glyphs, not dictionary entries |
| 81:F0E5 | `CPY #$C112` | `CPY #$C312` | menu upload buffer 7E:B312 flushes every 64 cells (English party-name pool is 60 cells) |
| 82:80BD | `JSL $80CE0E` (combat font LZ 82:CCD3 -> 7F:D800) | plate_font | then copies the player's ($14B0) and enemy's ($14B1+$20) precomposed names ($FF:8000, tools/gfx_plates.py) into font tiles $60-$6F |
| 82:87DA | `LDY $C6BD,x / STY $0F / LDY $C6BB,x` | plate_ptrs | combat name plate draws the fixed codes $C0-$C7 (player, map $3C48) / $C8-$CF (enemy, $3EF0) at 82:C85B instead of the packed kana name |

Data:
- $E0:8000 FARSHORT table; $E0:C000 English font (96 glyphs x 14 LE row words); $E0:CC00 advance widths; $E0:D000 code.
- $FF:8000 combat name plates (128 bytes per packed name index: 8 tiles x 8 rows x body/shadow masks); $FF:F000 plate code.
  Bank $FF is outside the text area (build.py TEXT_END).
- $E1:8000 precomposed UI cells (28 bytes each, code 0xB00 + n); $E1:E000-FFFF relocated UI strings.
- $E2 = copy of bank $84 (string tables; refs at 0xF47C, 0x21302, 0x22CF7, 0x25A93 point here); new strings $E2:F000+.
- $E3-$FF English dialogue text (deduplicated), from file 0x318000.

WRAM 7E:1E00-1E5F (zero in every RAM dump taken): V_EN flag, saved text context, VWF row buffer, composed glyph.

Battle command buttons: OBJ 4bpp at 0x4DABC redrawn by tools/gfx_buttons.py. Allowed write ranges: tools/allowed_ranges.txt.
