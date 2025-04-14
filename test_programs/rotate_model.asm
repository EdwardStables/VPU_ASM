    MOV 0       ; Ensure vectors are all zeroed
    STW SP 0    ; Translation Vector X,Y
    STW SP 4    ;                    Z,W
    STW SP 8    ; Rotation Vector    X,Y
    STW SP 12   ;                    Z,W
    STW SP 16   ; Offset Vector      X,Y
    STW SP 20   ; (account for rotation center) Z,W

    MOV R8 32  ; Final increment
    MOV R7 0   ; Start increment


    ; Adjust translation vector by (78,80,0)
    P.MAT.DST SP 0
    P.MAT.COL 2        ; offset y by 80
    MOV ACC 0x800
    P.MAT.OPR SET_VEC
    P.MAT.DST SP 0
    P.MAT.COL 1        ; offset x by 78
    MOV ACC 0x780
    P.MAT.OPR SET_VEC
    
    ; Adjust offset vector by (-39,-63,-30) (model center)
    P.MAT.DST SP 0x10
    P.MAT.DST SP 0x10
    P.MAT.COL 1        ; Set it to X=-63
    MOV ACC -1000
    P.MAT.OPR SET_VEC
    P.MAT.COL 2        ; Set it to Y=-39
    MOV ACC -624
    P.MAT.OPR SET_VEC
    P.MAT.COL 3        ; Set it to Z=-30
    MOV ACC -480
    P.MAT.OPR SET_VEC
    
    ; Clear screen to black
    P.BLI.COL 0x0
    P.SCH.FNC

LOOP:
    ; Update rotation vector each loop
    P.MAT.DST SP 8     ; Rotation vector at SP+8
    MOV ACC R7         ; Rotate by the value in R7
    P.MAT.COL 1        ; Changing X
    P.MAT.OPR SET_VEC
    P.MAT.COL 2        ; Changing Y
    P.MAT.OPR SET_VEC
    
    ; Set the location of the actual transformation matrix to be SP=0x18
    ; and initialise to the identity matrix
    P.MAT.DST SP 0x18
    P.MAT.OPR IDENTITY_MAT
    
    ; Apply the prepared translation, rotation, and offset vectors
    P.MAT.SRC1 SP 0x10   ; Offset
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR TRANSLATE
    P.MAT.SRC1 SP 0x8    ; Rotation
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR ROTATE
    P.MAT.SRC1 SP 0      ; Translation
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR TRANSLATE

    ; Submit the transformation to the render pipe
    MOV ACC SP
    ADD 0x18
    P.REN.TRN ACC

    ; Drive the render itself
    LBA R1 .DATA.0 ; Get the location of the object
    P.BLI.CLR      ; Clear the screen (could be earlier to avoid less blank cycles)
    P.SCH.FNC      ; Fence the clear
    P.REN.STR R1   ; Stream render operation
    P.SCH.FNC      ; Wait for this to finish
    P.BLI.SWP      ; Buffer swap (in simulation drives image dump)

    ; Update the rotation counter
    MOV ACC R7
    ADD 1
    MOV R7 ACC
    
    ; Loop terminates after a full rotation
    CMP R7 R8
    BRA END
    JMP LOOP

END:
    P.SCH.FNC
    HLT
