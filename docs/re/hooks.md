# Engine hooks (asm/dk4.asm, asar 1.91, applied by build.py after the data writes)

| Site | Original | Hook | Purpose |
|---|---|---|---|
| 80:B318 | `STY $30,x / SBC #$06CC` (dictionary call) | far_hook | codes 0x833-0xAFF: short far text call via FARSHORT ($E0:8000, 4 bytes: ptr24 + skip8); 0x0F b0 b1 b2 s0 s1: long far call (skip16); 0xEFF: far return; 0xB00-0xDFF: precomposed cell drawn as a glyph |
| 80:AEAE | glyph routine entry | vwf_hook | in far (English) text: compose one 16-px cell from ASCII letters (VWF with carry into the next cell; 0x7F flushes the carry); precomposed cells from $E1:8000 |
| 80:B169 | menu renderer `CMP #$06CC` | b160_hook | precomposed codes take the single-glyph path |
| 80:B1B0 | menu glyph draw | b1b0_hook | precomposed codes read their cell from $E1:8000 |
| 80:C3F0 | op 21 unit-info printer `CMP #$06CC` | c3f0_hook | precomposed codes are glyphs, not dictionary entries |
| 81:F0E5 | `CPY #$C112` | `CPY #$C312` | menu upload buffer 7E:B312 flushes every 64 cells (English party-name pool is 60 cells) |

Data:
- $E0:8000 FARSHORT table; $E0:C000 English font (96 glyphs x 14 LE row words); $E0:CC00 advance widths; $E0:D000 code.
- $E1:8000 precomposed UI cells (28 bytes each, code 0xB00 + n); $E1:E000-FFFF relocated UI strings.
- $E2 = copy of bank $84 (string tables; refs at 0xF47C, 0x21302, 0x22CF7, 0x25A93 point here); new strings $E2:F000+.
- $E3-$FF English dialogue text (deduplicated), from file 0x318000.

WRAM 7E:1E00-1E5F (zero in every RAM dump taken): V_EN flag, saved text context, VWF row buffer, composed glyph.

Battle command buttons: OBJ 4bpp at 0x4DABC redrawn by tools/gfx_buttons.py. Allowed write ranges: tools/allowed_ranges.txt.
