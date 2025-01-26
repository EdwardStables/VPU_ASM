    ; Make a matrix with numbers 1-16
    
    P.MAT.DST SP 0         ; Write to SP
    P.MAT.OPR IDENTITY_MAT ; Set to identity
    
    MOV 0x20        ; Set 1,2 to 2
    P.MAT.ROW 1
    P.MAT.COL 2
    P.MAT.OPR SET_MAT
    MOV 0x30        ; Set 1,3 to 3
    P.MAT.COL 3
    P.MAT.OPR SET_MAT
    MOV 0x40        ; Set 1,4 to 4
    P.MAT.COL 4
    P.MAT.OPR SET_MAT

    MOV 0x40        ; Add 4 to first row and copy to 2nd row
    P.MAT.SRC1 SP 0
    P.MAT.DST SP 8
    P.MAT.OPR ADD_VEC_SCALAR
    
    P.MAT.SRC1 SP 8 ; Add 4 to the 2nd row and copy to the 3rd row
    P.MAT.DST SP 16
    P.MAT.OPR ADD_VEC_SCALAR
    
    P.MAT.SRC1 SP 16; Add 4 to first row and copy to 4th row
    P.MAT.DST SP 24
    P.MAT.OPR ADD_VEC_SCALAR

    P.SCH.FNC
    HLT