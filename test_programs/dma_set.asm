    ;
    ; Set address 0xFFF00000 to 0xFFF10000 to 0xFF
    ;

    MOV 0xF             ; 0xF in ACC
    LSL 20              ; 0x00F00000 in ACC
    P.DMA.DST ACC
    
    MOV 0x10000         ; Length is 0x10000
    P.DMA.LEN ACC
    
    MOV 0xFF            ; Set all bytes to 0xFF
    P.DMA.SET ACC       
    
    P.SCH.FNC
    HLT