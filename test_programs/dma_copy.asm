    ;
    ; Set address 0xFFF00000 to 0xFFF0FFFF to 0xFF
    ;

    ;Lower range start in R1
    MOV 4095            ; 0xFFF in ACC
    LSL 20              ; 0xFFF00000 in ACC
    MOV R1 ACC          ; Move to R1
    
    ;Higher range start in R2
    MOV 4095            ; 0xFFF in ACC
    LSL 20              ; 0xFFF00000 in ACC
    ADD 458752          ; Offset to 0xFFF70000
    MOV R2 ACC          ; Move to R2

    ;Length in R3
    MOV 65535           ; Length is 0x10000
    MOV ACC R3
    
    ;Byte value in R4
    MOV R4 15
    
    ;Set first range to byte value
    P.DMA.DST R1
    P.DMA.LEN R3
    P.DMA.SET R4

    ;Repeat setup but for copy 
    P.DMA.DST R2
    P.DMA.SRC R1
    P.DMA.LEN R3
    P.DMA.CPY

    P.SNC.FNC
    HLT
    