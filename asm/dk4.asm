; Dragon Knight 4 (SFC) English engine: far text calls + VWF cells for the dialogue renderer.
; Assembled with asar 1.91 onto the 4 MB build image (banks $E0-$FF = file 0x300000-0x3FFFFF, expanded area).
; Hook list and data layout: docs/re/hooks.md.
lorom

; ---- WRAM (7E:1E00-1E5F, constant zero in every RAM dump taken; see docs/re/hooks.md) ----
!V_EN       = $7E1E00   ; byte: 1 = far (English) text active
!V_CODE     = $7E1E02   ; word
!V_SBASE    = $7E1E04   ; word: saved ctx $09
!V_SBANK    = $7E1E06   ; byte: saved ctx $0B
!V_SRET     = $7E1E08   ; word: return offset into the block
!V_TMP      = $7E1E0A   ; word
!V_TMP2     = $7E1E0C   ; word
!V_X        = $7E1E0E   ; word, signed: pen x inside the cell
!V_CC       = $7E1E10   ; word: carried letter code (0 = none)
!V_CX       = $7E1E12   ; word, signed: carried letter x (negative)
!V_GP       = $7E1E14   ; word: glyph data offset
!V_SH       = $7E1E16   ; word temp
!V_SH2      = $7E1E18   ; word temp
!V_ROWS     = $7E1E20   ; 14 words (bit 15 = leftmost px)
!V_GLYPH    = $7E1E40   ; 28 bytes, game font format

!FARSHORT   = $E08000   ; short-call table: (code - $833) * 3 -> 24-bit ptr; written by build.py
!FONT       = $E0C000   ; 96 glyphs (codes $20-$7F) x 14 little-endian row words; written by build.py
!FONTW      = $E0CC00   ; 96 advance widths (hi-res px); written by build.py
!PRE_FIRST  = $0B00     ; precomposed English UI cells: codes $0B00-$0E5F -> 28-byte cells at $E1:8000-$DFFF
!PRE_END    = $0E60     ; tools/ui.py PRE_END
!PRE_BANK   = $E1

; ===================== hooks =====================
org $80B318             ; dictionary call path (code >= $6CC): STY $30,x / SBC #$06CC
    JML far_hook

org $80AEAE             ; glyph routine entry: PHB / REP #$21 / LDY #$8800
    JML vwf_hook

org $80ACDF             ; text cursor advance: INC $06,x / LDA $06,x (col; wraps at width $05, line $08)
    JML adv_hook

org $80C93C             ; choice cursor: attribute rows for the new / old option (see choice_w)
    LDY.w #choice_hi
org $80C945
    LDY.w #choice_lo
org $80C95D
    JSL choice_w
    NOP
    NOP
    NOP
org $80C96C
    LDA.b #choice_hi>>16
org $80C976
    JSL choice_w
    NOP
    NOP
    NOP
org $80C984
    LDA.b #choice_hi>>16

org $80CA44             ; choice layout 1 (unused in JP): option tilemap offsets $0040,$0080 (rows 1-2, part of
    dw $CA54            ; layout 2's list at 80:CA52) = a 1-line question and its 2 options in one box (build.py)
org $80CA79             ; choice layout 1 option count (80:CA78)
    db $02

; unit pick lists (op 30 02 party split "choose up to 5 besides Rhea", op 30 08): 2 columns, 6 names in the box
; instead of 1 column of 3 (issue #5). Index i sits at row i/2, column i&1 (see list_pos).
org $85852A             ; draw (op 30 02): REP #$20 / ASL x5 / ADC #$D9E7 / STA $03 (name tiles), then JSR $8572
    JSL list_draw
    NOP #8
org $858445             ; draw (op 30 08): same sequence, then JSR $848D
    JSL list_draw
    NOP #8
org $8582A1             ; "picked" tag: XBA / LSR / LSR / ADC #$1807 (VRAM word address of index $23)
    JSL list_tag
    NOP #2
org $858323             ; highlight off (old index $25): XBA / LSR / LSR / ADC #$1809
    JSL list_name
    NOP #2
org $858340             ; highlight on (index $23)
    JSL list_name
    NOP #2
org $85832F             ; highlight off: LDA #$83CB / STA $0F (8 attribute bytes $24, bank $85)
    JSL list_attr_off
    NOP
org $85834C             ; highlight on: LDA #$83C3 / STA $0F (8 x $20)
    JSL list_attr_on
    NOP
org $85839A             ; highlight DMA source bank (85:838E, both rows) -> the attribute bytes built in WRAM
    db $7E
org $8583B7
    db $7E
org $858356             ; scroll: LDA $23 / SEC / SBC $24 ($24 = top row, 3 rows shown)
    JSL list_rowdiff
    NOP
org $8582FC             ; pad table (JSR ($82F6,x), x = $AB): right ($06) -> forward, left ($0E) -> back
    dw $830A
org $858304
    dw $8313
org $85830A             ; forward (down $0A: +2, right: +1 from the left column)
    JSL list_fwd
    RTS
org $858313             ; back (up $02: -2, left: -1 from the right column)
    JSL list_back
    RTS

org $80B169             ; menu string renderer: CMP #$06CC / BCC single glyph (else dictionary)
    JML b160_hook
    NOP

org $80B1B0             ; menu glyph draw: PHB / LDX #$8800
    JML b1b0_hook

org $80C3F0             ; unit-info box string printer (op 21): CMP #$06CC / BCS dictionary
    JML c3f0_hook
    NOP

org $80C253             ; unit-info box: LDY #defense_label / STY $00 right after a digit print left $02 = #$80
    JSL c253_fix
    NOP

org $81F0FC             ; menu-string buffer flush (JSR from 81:F0B5): a second flush lost the string index $1F
    JML pool_flush      ; during its frame wait (full-width party names = 2 flushes); see pool_flush

org $81F0E5             ; menu-string upload buffer 7E:B312: flush every 64 cells instead of 56 (the English
    CPY #$C312          ; party-name pool is 60 cells; 7E:C112-C312 is unused, zero in every RAM dump)

org $8280BD             ; combat screen setup: JSL lz (font block 82:CCD3 -> 7F:D800); names: tools/gfx_plates.py
    JSL plate_font

org $8287DA             ; combat name plate: LDY $C6BD,x / STY $0F / LDY $C6BB,x (packed kana string bounds)
    JSL plate_ptrs
    NOP
    NOP
    NOP
    NOP

; ===================== code =====================
org $E0D000
far_hook:               ; M=16 X=16, A = code, Y = offset after the 2-byte code, X = text ctx, carry set
    CMP #$0833
    BCS .mine
    SEC
    STY $30,x
    SBC #$06CC
    JML $80B31D
.mine:
    CMP #$0EFF
    BNE +
    JMP .ret
+   CMP #$0F00
    BCS .long
    CMP #!PRE_FIRST     ; precomposed UI cells drawn as one glyph (80:B2DB: SEP, STY $0C,x, JSR glyph)
    BCC +
    JML $80B2DB
+
    SEC                 ; short: (code - $833) * 4 indexes FARSHORT: ptr24, skip8
    SBC #$0833
    ASL A
    ASL A
    PHX
    TAX
    LDA.l !FARSHORT,x
    STA !V_TMP          ; ptr lo16
    LDA.l !FARSHORT+2,x
    STA !V_TMP2         ; lo = bank, hi = skip
    PLX
    AND #$FF00
    XBA
    STA !V_SH           ; skip
    BRA .call
.long:                  ; 0F b0 b1 b2 s0 s1: ptr = b0 | b1 << 8 | b2 << 16, skip16 = bytes after the token
    AND #$00FF
    STA !V_TMP
    LDA [$00],y         ; lo = b1, hi = b2
    INY
    INY
    STA !V_TMP2
    AND #$00FF
    XBA
    ORA !V_TMP
    STA !V_TMP          ; ptr lo16
    LDA !V_TMP2
    XBA
    STA !V_TMP2         ; lo = bank
    LDA [$00],y
    STA !V_SH           ; skip (counted from the end of the 4-byte token)
.call:                  ; V_TMP = ptr lo16, V_TMP2 lo = bank, V_SH = bytes to skip after the token
    TYA
    CLC
    ADC !V_SH
    STA !V_SRET
    LDA $09,x
    STA !V_SBASE
    SEP #$20
    LDA $0B,x
    STA !V_SBANK
    LDA !V_TMP2
    STA $0B,x
    REP #$20
    LDA !V_TMP
    STA $09,x
    STZ $0C,x
    LDA #$0000
    STA !V_CC
    SEP #$20
    LDA #$01
    STA !V_EN
    JML $80B2B6
.ret:
    SEP #$20
    LDA !V_SBANK
    STA $0B,x
    LDA #$00
    STA !V_EN
    REP #$20
    LDA !V_SBASE
    STA $09,x
    LDA !V_SRET
    STA $0C,x
    LDA #$0000
    STA !V_CC
    SEP #$20
    JML $80B2B6

; ---------------------------------------------------------------------------------
; M=8 X=16, X = ctx. English lines may use all 24 cells (JP lines use 23). Drawing cell 24 wrapped the line at
; once; on a page's last line that flagged page-full, so a wait op after the text showed an empty page (issue #5).
; In far text, a glyph-loop advance (JSR from 80:AB23 / 80:AB2D) that reaches the width leaves col = width
; pending; the next 00 newline (80:B302: col != 0, col = width - 1, advance) wraps as usual.
adv_hook:
    INC $06,x
    LDA.l !V_EN
    BEQ .orig
    REP #$20
    LDA $01,s           ; JSR return address - 1
    CMP #$AB25
    BEQ .glyph
    CMP #$AB2F
    BEQ .glyph
    SEP #$20
.orig:
    LDA $06,x
    JML $80ACE3         ; CMP $05,x ...
.glyph:
    SEP #$20
    LDA $06,x
    CMP $05,x
    BNE .orig
    JML $80ACF8         ; no wrap: only recompute the cell address
vwf_hook:               ; M=8 X=16, C = code, X = ctx, $00-$02 = text base, ctx $0C = next offset
    PHB
    REP #$21
    STA !V_CODE
    LDA !V_EN
    AND #$00FF
    BEQ .jp
    LDA !V_CODE
    CMP #$0080
    BCS .jp
    CMP #$0020
    BCC .jp
    JSR compose
    LDA.w #!V_GLYPH
    STA $00
    SEP #$20
    LDA #$7E
    STA $02
    JML $80AED7         ; original tail: copy 28 bytes from [$00] to the cell buffer, shadow, advance
.jp:
    LDA !V_CODE
    CMP #!PRE_FIRST
    BCC +
    CMP #!PRE_END
    BCS +
    JSR pre_ptr         ; precomposed English cell -> [$00]
    STA $00
    SEP #$20
    LDA.b #!PRE_BANK
    STA $02
    JML $80AED7
+   LDY #$8800
    CLC
    JML $80AEB4

; A (16-bit) = precomposed code -> A = ROM address low 16 of its 28-byte cell
pre_ptr:
    SEC
    SBC #!PRE_FIRST
    STA !V_SH
    ASL A
    ASL A
    STA !V_SH2          ; *4
    ASL A
    ASL A
    ASL A               ; *32
    SEC
    SBC !V_SH2          ; *28
    CLC
    ADC #$8000
    RTS

c3f0_hook:              ; M=16, A = 2-byte code: precomposed cells are glyphs, not dictionary entries
    CMP #!PRE_FIRST
    BCC .orig
    CMP #!PRE_END
    BCS .orig
    JML $80C3F5         ; SEP #$20 / draw one cell
.orig:
    CMP #$06CC
    BCS +
    JML $80C3F5
+   JML $80C40F

c253_fix:               ; M=8: [$00] = relocated "{Defense}" label ($E1, pointer word written by tools/ui.py)
    LDA #$E1
    STA $02
    LDA.l $E1DFFE
    STA $00
    LDA.l $E1DFFF
    STA $01
    RTL

b160_hook:              ; M=16, A = code. Precomposed cells take the single-glyph path.
    CMP #!PRE_FIRST
    BCC .orig
    CMP #!PRE_END
    BCS .orig
    JML $80B1A9
.orig:
    CMP #$06CC
    BCS +
    JML $80B1A9
+   JML $80B16E

b1b0_hook:              ; M=16 X=16, A = code, Y = cell buffer
    PHB
    CMP #!PRE_FIRST
    BCC .orig
    CMP #!PRE_END
    BCS .orig
    JSR pre_ptr
    STA $48
    SEP #$20
    LDA.b #!PRE_BANK
    STA $4A
    JML $80B1E0
.orig:
    LDX #$8800
    JML $80B1B4

; compose one 16-px cell from the text stream into V_GLYPH. M=16 X=16, X = ctx preserved.
compose:
    PHX
    LDA #$0000
    LDX #$001A
-   STA !V_ROWS,x
    DEX
    DEX
    BPL -
    PLX
    LDA #$0000
    STA !V_X
    LDA !V_CC
    BEQ .noc
    STA !V_TMP          ; carried letter first, at its negative x
    LDA !V_CX
    STA !V_X
    JSR draw
    LDA #$0000
    STA !V_CC
.noc:
    LDA !V_CODE
.loop:
    CMP #$007F
    BEQ .done           ; flush cell: only the carry
    STA !V_TMP
    LDA !V_X
    STA !V_TMP2         ; x before this letter
    JSR draw
    LDA !V_X
    CMP #$0010
    BEQ .done
    BMI .peek           ; x < 16
    LDA !V_TMP          ; letter overflows: carry it into the next cell at x - 16
    STA !V_CC
    LDA !V_TMP2
    SEC
    SBC #$0010
    STA !V_CX
    BRA .done
.peek:
    LDY $0C,x
    LDA [$00],y
    AND #$00FF
    CMP #$0020
    BCC .done
    CMP #$007F
    BCS .done
    INY
    PHA
    TYA
    STA $0C,x           ; consume it
    PLA
    BRA .loop
.done:
    PHX
    LDY #$0000
.cv:
    TYA
    ASL A
    TAX
    LDA !V_ROWS,x
    STA !V_TMP
    TYX
    LDA.l lidx,x
    AND #$00FF
    TAX
    SEP #$20
    LDA !V_TMP+1
    STA !V_GLYPH,x
    REP #$20
    TYX
    LDA.l ridx,x
    AND #$00FF
    TAX
    SEP #$20
    LDA !V_TMP
    STA !V_GLYPH,x
    REP #$20
    INY
    CPY #$000E
    BCC .cv
    PLX
    RTS

lidx: db 0,1,2,3,4,5,6,7,16,17,18,19,20,21,0,0
ridx: db 8,9,10,11,12,13,14,15,22,23,24,25,26,27,0,0

; draw letter V_TMP ($20-$7E) at signed x V_X into V_ROWS; V_X += advance width. M=16 X=16, X preserved.
draw:
    PHX
    LDA !V_TMP
    SEC
    SBC #$0020
    ASL A
    ASL A
    STA !V_SH           ; idx * 4
    ASL A
    ASL A
    ASL A               ; idx * 32
    SEC
    SBC !V_SH
    STA !V_GP           ; idx * 28
    LDY #$0000
.row:
    LDA !V_GP
    TAX
    LDA.l !FONT,x
    STA !V_SH2
    LDA !V_X
    BMI .neg
    TAX
    LDA !V_SH2
-   CPX #$0000
    BEQ .or
    LSR A
    DEX
    BRA -
.neg:
    EOR #$FFFF
    INC A
    TAX
    LDA !V_SH2
-   CPX #$0000
    BEQ .or
    ASL A
    DEX
    BRA -
.or:
    TYX
    ORA !V_ROWS,x
    STA !V_ROWS,x
    LDA !V_GP
    INC A
    INC A
    STA !V_GP
    INY
    INY
    CPY #$001C
    BCC .row
    LDA !V_TMP
    SEC
    SBC #$0020
    TAX
    LDA.l !FONTW,x
    AND #$00FF
    CLC
    ADC !V_X
    STA !V_X
    PLX
    RTS

; ---------------------------------------------------------------------------------
; choice cursor (80:C92F): the moved-to / moved-from option gets attribute bytes $20 (white) / $24 (grey) over 10
; cells from 80:CA64 / 80:CA6E. English options run longer ("Necromancer's Squad" kept a white "d", issue #5):
; recolor 13 cells at column 0 (up to the second column) or up to the box edge (24 - column), from these tables.
choice_w:               ; M=8 X=16, replaces TDC / LDA #$0A / JSL $809731 (A = DMA length), $17 = option's
    REP #$20            ; tilemap address, $03 = box origin
    LDA $17
    SEC
    SBC $03
    AND #$001F          ; column (0 or 13)
    BNE +
    LDA #$000D
    BRA ++
+   EOR #$FFFF
    SEC
    ADC #$0018          ; 24 - column
++  SEP #$20
    JSL $809731
    RTL
choice_hi:
    db $20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20,$20
choice_lo:
    db $24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24,$24

; ---------------------------------------------------------------------------------
; unit pick lists (85:81A7 / 85:8148, shared input loop 85:8204): 2 columns. Tilemap: 32 words per tile row,
; 2 tile rows per entry; column 0 = tag at word 7, name (8 tiles) at word 9; column 1 is 12 words to the right.
list_pos:               ; M=16, A = index (high byte 0) -> A = row * $40 + column * $0C, carry clear
    LSR A
    BCS +
    XBA
    LSR A
    LSR A
    RTS
+   XBA
    LSR A
    LSR A               ; low bits shifted out are 0: carry clear
    ADC.w #$000C
    RTS
list_tag:
    JSR list_pos
    ADC.w #$1807
    RTL
list_name:
    JSR list_pos
    ADC.w #$1809
    RTL
list_draw:              ; M=8 -> 16: $03 = name tiles of unit A (as the original), $00 = buffer slot of index $1F
    REP #$20
    ASL A
    ASL A
    ASL A
    ASL A
    ASL A
    ADC.w #$D9E7
    STA $03
    LDA $1F
    AND.w #$00FF
    JSR list_pos
    ASL A
    ADC.w #$E012        ; 7F:E012 = row 0, word 9
    STA $00
    RTL
; highlight attribute bytes (tilemap high bytes): the original wrote a flat $20 / $24 over the 8 name tiles, which
; zeroed tile-number bits 8-9; full-width names reach tile $1F3. Keep each tile's bits 8-9 from the list tilemap
; copy at 7F:E000 (= VRAM $1800). M=16 X=16, $11 = VRAM word address of the name's top row.
!LIST_ATTR = $1E20      ; 8 bytes in 7E:1E20 (V_ROWS: VWF scratch, idle while a list is open)
list_attr_off:
    LDA.w #$0024
    BRA list_attr
list_attr_on:
    LDA.w #$0020
list_attr:
    PHX
    PHY
    PHA
    LDA $11
    SEC
    SBC.w #$1800
    ASL A
    TAX
    LDY.w #$0000
-   LDA $7FE001,x       ; low byte = high byte of the tile word
    AND.w #$0003
    ORA $01,s
    SEP #$20
    STA.w !LIST_ATTR,y  ; DB = $7E (85:800E)
    REP #$20
    INX
    INX
    INY
    CPY.w #$0008
    BNE -
    PLA
    LDA.w #!LIST_ATTR
    STA $0F
    PLY
    PLX
    RTL
list_rowdiff:           ; M=8: A = row of $23 - top row $24, flags for the BMI / CMP #$03 after it
    LDA $23
    LSR A
    SEC
    SBC $24
    RTL
list_fwd:               ; M=8: carry set = no move
    LDA $AB
    CMP.b #$06
    BNE +
    LDA $23
    BIT.b #$01
    BNE .no             ; right from the right column
    INC A
    BRA ++
+   LDA $23
    INC A
    INC A
++  CMP $1F
    BCS .no
    STA $23
    CLC
    RTL
.no:
    SEC
    RTL
list_back:
    LDA $AB
    CMP.b #$0E
    BNE +
    LDA $23
    BIT.b #$01
    BEQ .no             ; left from the left column
    DEC A
    BRA ++
+   LDA $23
    SEC
    SBC.b #$02
    BMI .no
++  STA $23
    CLC
    RTL
.no:
    SEC
    RTL

; 81:F0FC copied (M=8 X=16, Y = buffer end): upload 7E:B312..Y to VRAM $21, $21 += words. The JP pool fit one
; flush; a second one refilled the buffer before the first upload ran (both VRAM halves got the second batch):
; wait a frame after queueing it. Keeps the string index $1F too. Returns through 81:F154 (RTS) into bank 81.
pool_flush:
    PEI ($1F)
    LDA $6F
    BPL .now
    REP #$20            ; queued (NMI) upload
    TYA
    SEC
    SBC.w #$B312
    TAY
    PHA
    SEP #$20
    LDX.w #$B312
    STX $45
    LDA.b #$7E
    STA $47
    LDX $21
    LDA.b #$80
    JSL $80986D
    BRA .done
.now:
    PHY
    LDX $21
    STX $45
    LDA.b #$7E
    STA $4A
    LDX.w #$B312
    STX $48
    REP #$20
    LDA $01,s
    SEC
    SBC.w #$B312
    STA $01,s
    TAY
    SEP #$20
    JSL $80911B
    LDA.b #$80
    TSB $AF
    TDC
    JSL $809769
    LDA.b #$80
    TRB $AF
.done:
    JSL $80911B         ; the upload runs at the next NMI: let it read the buffer before it is refilled
    REP #$20
    PLA
    LSR A
    CLC
    ADC $21
    STA $21
    PLA
    STA $1F
    SEP #$20
    JML $81F154         ; RTS
assert pc() <= $E0E000

; ---------------------------------------------------------------------------------
; combat name plates: precomposed names at $FF:8000 (128 bytes per packed name index, tools/gfx_plates.py)
!PLATES     = $FF8000

org $FFF000
plate_ptrs:             ; M=16 X=16, A = plate tilemap address - $20: 82:87D0 draws the fixed codes at 82:C85B
    CMP #$3C28          ; player plate (82:8726); the enemy plate is $3EF0
    BNE .enemy
    LDY #$C863
    STY $0F
    LDY #$C85B          ; $C0-$C7 -> font tiles $60-$67
    RTL
.enemy:
    LDY #$C86B
    STY $0F
    LDY #$C863          ; $C8-$CF -> font tiles $68-$6F
    RTL

plate_font:             ; M=16 X=16: decompress the font, then the two names into its tiles $60-$6F (7F:E400)
    JSL $80CE0E
    PHP
    PHB
    REP #$30
    LDA.l $0014B0       ; player unit
    AND #$00FF
    LDY #$E400
    JSR plate_draw
    LDA.l $0014B1       ; enemy unit: packed index + $20, none from $B0 up (82:8730)
    AND #$00FF
    CMP #$00B0
    BCS +
    ADC #$0020
    LDY #$E500
    JSR plate_draw
+   PLB
    PLP
    RTL

plate_draw:             ; M=16 X=16, A = packed name index, Y = destination in bank $7F (8 tiles, 4bpp)
    CMP #$00D0
    BCC +
    LDA #$0000
+   XBA
    LSR A               ; * 128
    TAX
    SEP #$20
    LDA #$7F
    PHA
    PLB
.row:                   ; body $D, shadow $E, background $6 (rows 0-3) / $7 (rows 4-7)
    LDA.l !PLATES+1,x
    ORA.l !PLATES,x
    STA $0011,y         ; plane 3: body | shadow
    LDA #$FF
    STA $0010,y         ; plane 2
    LDA.l !PLATES,x
    EOR #$FF
    STA $0001,y         ; plane 1: not body
    TXA
    AND #$08
    BEQ +
    LDA.l !PLATES+1,x
    EOR #$FF            ; plane 0, rows 4-7: not shadow
    BRA ++
+   LDA.l !PLATES,x     ; plane 0, rows 0-3: body
++  STA $0000,y
    INX
    INX
    INY
    INY
    TXA
    AND #$0F
    BNE .row
    REP #$21            ; next tile: skip planes 2-3
    TYA
    ADC #$0010
    TAY
    SEP #$20
    TXA
    AND #$7F
    BNE .row
    REP #$30
    RTS
