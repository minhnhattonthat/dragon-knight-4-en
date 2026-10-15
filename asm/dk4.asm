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
!PRE_FIRST  = $0B00     ; precomposed English UI cells: codes $0B00-$0DFF -> 28-byte cells at $E1:8000
!PRE_END    = $0E00
!PRE_BANK   = $E1

; ===================== hooks =====================
org $80B318             ; dictionary call path (code >= $6CC): STY $30,x / SBC #$06CC
    JML far_hook

org $80AEAE             ; glyph routine entry: PHB / REP #$21 / LDY #$8800
    JML vwf_hook

org $80B169             ; menu string renderer: CMP #$06CC / BCC single glyph (else dictionary)
    JML b160_hook
    NOP

org $80B1B0             ; menu glyph draw: PHB / LDX #$8800
    JML b1b0_hook

org $80C3F0             ; unit-info box string printer (op 21): CMP #$06CC / BCS dictionary
    JML c3f0_hook
    NOP

org $81F0E5             ; menu-string upload buffer 7E:B312: flush every 64 cells instead of 56 (the English
    CPY #$C312          ; party-name pool is 60 cells; 7E:C112-C312 is unused, zero in every RAM dump)

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
