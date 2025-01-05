    P.BLI.COL 0x000000  ; Set blitter to black (RGB format)
    P.BLI.CLR

    P.BLI.COL 0xFF0000  ; Set blitter to white (RGB format)

    MOV R1 0x8
    MOV R2 0x8
    P.BLI.SPS R1 R2     ; Start writing text at 8,8

    ; "Hello World" on one line, then the entire supported ASCII set

    P.BLI.SPC 72        ; Hello World
    P.BLI.SPC 101
    P.BLI.SPC 108
    P.BLI.SPC 108
    P.BLI.SPC 111
    P.BLI.SPC 32
    P.BLI.SPC 87
    P.BLI.SPC 111
    P.BLI.SPC 114
    P.BLI.SPC 108
    P.BLI.SPC 100

    MOV ACC R2
    ADD 8
    MOV R2 ACC
    P.BLI.SPS R1 R2     ; Next line
    
    MOV R3 32           ; ASCII code to write
    MOV R5 8            ; Current line index
    MOV R6 12           ; Line count

LOOP:
    P.BLI.SPC R3        ; Write character

    MOV ACC R5
    ADD -1
    MOV R5 ACC

    MOV ACC R3
    ADD 1
    MOV R3 ACC

    CMP R5              ; Test for end of line
    BRA NEW_LINE
    JMP LOOP

NEW_LINE:
    MOV ACC R2
    ADD 8
    MOV R2 ACC
    P.BLI.SPS R1 R2
    MOV R5 8
    MOV ACC R6
    ADD -1
    MOV R6 ACC
    
    CMP R6
    BRA END
    JMP LOOP

END:
    P.BLI.SWP
    P.SCH.FNC
    HLT