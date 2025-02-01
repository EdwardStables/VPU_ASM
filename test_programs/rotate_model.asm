    MOV 0       ; Ensure vectors are all zeroed
    STW SP 0
    STW SP 4
    STW SP 8
    STW SP 12
    STW SP 16
    STW SP 20

    MOV R8 32  ; Final increment
    MOV R7 0   ; Start increment


    P.MAT.DST SP 0     ; Translation vector at SP+0 
    P.MAT.COL 2        ; Set it to Y=90
    MOV ACC 0x900
    P.MAT.OPR SET_VEC
    P.MAT.DST SP 0     ; Translation vector at SP+0 
    P.MAT.COL 1        ; Set it to X=88
    MOV ACC 0x580
    P.MAT.OPR SET_VEC
    
    P.MAT.DST SP 0x10  ; Object offset vector
    P.MAT.COL 1        ; Set it to Z=-30
    MOV ACC -480
    P.MAT.OPR SET_VEC
    
    ; Rotation vector at SP+8, starts valued at zero

    P.BLI.COL 0x0
    P.SCH.FNC

LOOP:
    P.MAT.DST SP 8     ; Rotation vector at SP+8
    P.MAT.COL 1        ; Changing X
    MOV ACC R7         ; Rotate by the value in R7
    P.MAT.OPR SET_VEC
    P.SCH.FNC
    
    P.MAT.DST SP 0x18  ; Actual translation is at SP+0x18
    P.MAT.OPR IDENTITY_MAT
    
    ;P.MAT.SRC1 SP 0x10      ; Object local translation to change axis
    ;P.MAT.SRC2 SP 0x18
    ;P.MAT.DST SP 0x10
    ;P.MAT.OPR TRANSLATE
    P.MAT.SRC1 SP 0      ; Then translation
    P.MAT.SRC2 SP 0x10
    P.MAT.DST SP 0x10
    P.MAT.OPR TRANSLATE
    P.MAT.SRC1 SP 0x8    ; Then 
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR ROTATE

    MOV ACC SP     ; Result of transformation matrices is at SP+0x10
    ADD 0x18
    P.REN.TRN ACC  ; Apply the transformation
    
    LBA R1 .DATA.0 ; Do the actual render
    P.BLI.CLR
    P.SCH.FNC
    P.REN.STR R1
    P.SCH.FNC
    P.BLI.SWP

    MOV ACC R7     ; Update the counter
    ADD 1
    MOV R7 ACC
    
    CMP R7 R8      ; Stop when all iterations are done
    BRA END
    JMP LOOP

END:
    P.SCH.FNC
    HLT
