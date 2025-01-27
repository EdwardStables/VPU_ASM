
    P.MAT.DST SP 8         ; Writing just past the vector
    P.MAT.OPR IDENTITY_MAT ; Set to identity
    
    MOV 0       ; Ensure vector at SP is zeroed
    STW SP 0
    STW SP 4
    
    P.MAT.DST SP 0
    MOV ACC 128  ; Shift X by 64 (LSL for fixed point)
    LSL 4
    P.MAT.COL 1
    P.MAT.OPR SET_VEC

    P.MAT.SRC1 SP 0      ; Update with the translation
    P.MAT.SRC2 SP 8
    P.MAT.DST SP 8
    P.MAT.OPR TRANSLATE

    P.SCH.FNC

    MOV ACC SP           ; Apply the translation and do the draw call
    ADD 8
    P.REN.TRN ACC
    LBA R1 .DATA.0
    P.REN.STR R1
    
    P.SCH.FNC
    P.BLI.SWP
    P.SCH.FNC
    HLT
