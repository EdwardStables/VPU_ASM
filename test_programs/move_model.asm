
    P.MAT.DST SP 8         ; Writing just past the vector
    P.MAT.OPR IDENTITY_MAT ; Set to identity
    
    MOV 0       ; Ensure vector at SP is zeroed
    STW SP 0
    STW SP 4

    MOV R8 300  ; Final movement distance
    MOV R7 0    ; Start movement distance

    P.MAT.DST SP 0
    MOV ACC 3  ; Shift X by 3 (LSL for fixed point)
    LSL 4
    P.MAT.COL 1
    P.MAT.OPR SET_VEC

    P.BLI.COL 0x0

LOOP:
    P.MAT.SRC1 SP 0      ; Update with the translation
    P.MAT.SRC2 SP 8
    P.MAT.DST SP 8
    P.MAT.OPR TRANSLATE

    P.SCH.FNC

    MOV ACC SP           ; Apply the translation and do the draw call
    ADD 8
    P.REN.TRN ACC
    LBA R1 .DATA.0
    
    P.BLI.CLR
    P.SCH.FNC
    P.REN.STR R1
    
    P.SCH.FNC
    P.BLI.SWP

    P.SCH.FNC

    MOV ACC R7
    ADD 3
    MOV R7 ACC

    CMP R7 R8
    BRA END
    JMP LOOP

END:
    P.SCH.FNC
    HLT
