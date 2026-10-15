# Text engine (Dragon Knight 4, SFC, LoROM 3 MB, header says 4 MB / FastROM map 0x30)

## Font
- 1bpp 16x14 cells (glyph drawn in 14x14), 28 bytes/glyph at ROM 0x40000 (88:8000); index >= 0x492 continues
  at 89:8000 (0x48000). Layout: see tools/font.py. Glyph routine 80:AEAE (A = code); index = code - 0x11.
- Glyphs are frequency-ordered kana/kanji; transcription in tbl/glyphs_jp.txt (by eye; '*' marks look-alikes).
- Screen is 512-px hi-res: each 16-px cell is 8 lo-res px wide. Dialogue box: name line + 2 text lines,
  ~23 cells per line (JP lines are indented by one 0x11 blank).
- Renderer writes 0x40 bytes per char into a WRAM buffer ($1A,x): 4 2bpp tiles (TL rows0-7, TR rows0-7,
  BL rows 8-13, BR rows 8-13), plane 0 only; JSR 80:B013 queues the upload.

## Script blocks
- Table at ROM 0xBE16: 60 x (24-bit ptr, scene byte). Block = [len16][body]; 81:9615 copies body to 7F:0000.
  Entries 56-58 have bogus lengths that over-cover the next block (56 contains 57's len word).
- Body = [header of 16-bit entry offsets][object data][script]. First header word = script start.
  81:A0AF builds the NPC list from a ROM table (81:A53E by scene $0837): NPC i talk script = header word i.
- Text VM: 80:B2B6, context at X (0x0700), base ptr $09-$0B, offset $0C.
  - 00 newline (in dictionary mode: return); 11 blank cell; 12-FF glyph; 01-0F xx 16-bit glyph code.
  - code >= 0x6CC: dictionary call: 85:8ED0 table (359 entries, 16-bit ptrs into bank 85), entries 00-terminated,
    saves base in $2D-$30, flag 08 in $0700. Names in brackets (【カケル】) are dictionary entries 0x772+.
  - 10 op args: command; op table 80:B359 (ops 00-42), arg counts in tools/dk4.py ARGS. Byte fetch helper 80:B9AB.
  - Jumps are absolute 16-bit offsets in the 7F copy: ops 0A,12,14,32,35,40,41 (JUMP_ARG), op 0C = choice:
    layout byte, then CHOICE_N[layout]+1 targets (80:CA78), last = cancel.
  - Jump targets can land inside a text run (page starts): split runs there.
