    MOV 0xFFFFFF
    P.BLI.COL ACC       ; Set blitter to white (RGB format)

    MOV R1 0x1
    MOV R2 0x2
    P.BLI.PIX R1 R2     ; Set pixel (1,2) to white

    P.BLI.COL 0xFF0000  ; Set blitter to red (RGB format) with immediate

    MOV R1 150
    MOV R2 175
    P.BLI.PIX R1 R2     ; Set pixel (150,175) to red
    
    P.SCH.FNC
    HLT
