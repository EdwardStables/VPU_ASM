    ; Hard-code x offset
    ;  1  0  0 64
    ;  0  1  0  0
    ;  0  0  1  0
    ;  0  0  0  1
    MOV 0x00000010 ; Cell 0,0 and 0,1 -> 1,0
    STW SP 
    MOV 0x04000000 ; Cell 0,2 and 0,3 -> 0,64
    STW SP 4
    MOV 0x00100000 ; Cell 1,0 and 1,1 -> 0,1
    STW SP 8
    MOV 0          ; Cell 1,2 and 1,3 -> 0,0
    STW SP 12
    MOV 0          ; Cell 2,0 and 2,1 -> 0,0
    STW SP 16
    MOV 0x00000010 ; Cell 2,2 and 2,3 -> 1,0
    STW SP 20
    MOV 0          ; Cell 3,0 and 3,1 -> 0,0
    STW SP 24
    MOV 0x00100000 ; Cell 3,2 and 3,3 -> 0,1
    STW SP 28
    P.REN.TRN SP   ; Load the transform
    LBA R1 .DATA.0
    P.REN.STR R1   ; Render the model
    P.SCH.FNC
    P.BLI.SWP
    P.SCH.FNC
    HLT