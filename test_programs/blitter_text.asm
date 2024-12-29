    P.BLI.COL 0xFFFFFF  ; Set blitter to white (RGB format)

    MOV R1 0x8
    MOV R2 0x8
    P.BLI.SPS R1 R2     ; Start writing text at 8,8


    MOV 1               ; Write out 1-4 separated by spaces
    MOV R1 5
LOOP:
    P.BLI.SPC ACC
    P.BLI.SPC 0x20
    ADD 1
    CMP ACC R1
    BRA END
    JMP LOOP

END:
    P.SCH.FNC
    HLT