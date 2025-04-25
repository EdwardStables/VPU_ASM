    MOV 0       ; Ensure vectors at SP is zeroed
    STW SP 0x0
    STW SP 0x4
    STW SP 0x8
    STW SP 0xC
    STW SP 0x10
    STW SP 0x14

    ; Set translation vector (150,100,100)
    P.MAT.DST SP 0
    MOV ACC 150
    LSL 4
    P.MAT.COL 1
    P.MAT.OPR SET_VEC
    MOV ACC 100
    LSL 4
    P.MAT.COL 2
    P.MAT.OPR SET_VEC
    MOV ACC 100
    LSL 4
    P.MAT.COL 3
    P.MAT.OPR SET_VEC
    
    ; Set rotation vector (pi/2,0,0)
    P.MAT.DST SP 0x8
    MOV ACC 8
    P.MAT.COL 1
    P.MAT.OPR SET_VEC
    
    ; Set offset vector (-63,-40,-30)
    P.MAT.DST SP 0x10
    MOV ACC -63
    LSL 4
    P.MAT.COL 1
    P.MAT.OPR SET_VEC
    MOV ACC -40
    LSL 4
    P.MAT.COL 2
    P.MAT.OPR SET_VEC
    MOV ACC -30
    LSL 4
    P.MAT.COL 3
    P.MAT.OPR SET_VEC

    MOV R8 31
    MOV R7 0
    
LOOP:
    ; Set rotation vector, rotate around y every frame
    P.MAT.DST SP 8
    MOV ACC R7
    P.MAT.COL 2
    P.MAT.OPR SET_VEC

    P.MAT.DST SP 0x18      ; Writing just past the vector
    P.MAT.OPR IDENTITY_MAT ; Set to identity
    P.MAT.SRC1 SP 0x10     ; Update with the offset
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR TRANSLATE
    P.MAT.SRC1 SP 8       ; Update with the rotation
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR ROTATE
    P.MAT.SRC1 SP 0       ; Update with the translation
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR TRANSLATE

    P.SCH.FNC

    MOV ACC SP           ; Apply the translation and do the draw call
    ADD 0x18
    P.REN.TRN ACC
    LBA R1 .DATA.0

    ; Render frame
    P.BLI.COL 0
    P.BLI.CLR
    P.SCH.FNC
    P.REN.STR R1
    P.SCH.FNC
    P.BLI.SWP

    ; Loop update
    CMP R7 R8
    BRA END
    MOV ACC R7
    ADD 1
    MOV R7 ACC
    JMP LOOP
    
END:
    P.SCH.FNC
    HLT
