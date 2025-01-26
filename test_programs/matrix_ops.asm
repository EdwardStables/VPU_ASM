    ; Make a matrix with numbers 1-16
    
    P.MAT.DST SP 0         ; Write to SP
    P.MAT.OPR IDENTITY_MAT ; Set to identity
    
    MOV 2           ; Set 1,2 to 2
    P.MAT.ROW 1
    P.MAT.COL 2
    P.MAT.OPR SET_MAT
    ADD 1           ; Set 1,3 to 3
    P.MAT.COL 3
    P.MAT.OPR SET_MAT
    ADD 1           ; Set 1,4 to 3
    P.MAT.COL 4
    P.MAT.OPR SET_MAT

    ADD 1           ; Add 4 to first row and copy to 2nd row
    P.MAT.SRC1 SP 0
    P.MAT.DST SP 8
    P.MAT.OPR ADD_VEC_SCALAR
    ADD 4           ; Add 4 to first row and copy to 2nd row
    P.MAT.SRC1 SP 0
    P.MAT.DST SP 16
    P.MAT.OPR ADD_VEC_SCALAR
    ADD 4           ; Add 4 to first row and copy to 2nd row
    P.MAT.SRC1 SP 0
    P.MAT.DST SP 24
    P.MAT.OPR ADD_VEC_SCALAR

    P.SCH.FNC
    HLT