    P.BLI.COL 0xFFFFFF  ; Set blitter to white (RGB format)

    MOV R1 0x8
    MOV R2 0x8
    P.BLI.SPS R1 R2     ; Start writing text at 8,8
    P.BLI.SPC 0x23      ; Write #

    P.SCH.FNC
    HLT