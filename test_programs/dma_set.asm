    ;
    ; Set address 0xFFF00000 to 0xFFF10000 to 0xFF
    ;

    MOV 4095            ; 0xFFF in ACC
    LSL 20              ; 0xFFF00000 in ACC
    P.DMA.DST ACC
    
    MOV 65535           ; Length is 0x10000-1
    P.DMA.LEN ACC
    
    MOV 15              ; Set all bytes to 0xFF
    P.DMA.SET ACC       