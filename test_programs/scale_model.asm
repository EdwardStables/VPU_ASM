    MOV 0       ; Ensure vectors are all zeroed
    STW SP 0    ; Scale Vector X,Y
    STW SP 4    ;              Z,W

    MOV R8 8    ; Final increment
    MOV R7 1    ; Start increment

    ; Clear screen to black
    P.BLI.COL 0x0
    P.SCH.FNC

LOOP:
    ; Update scale vector each loop
    ; Set scale vector to (1,1,1) 
    P.MAT.DST SP 0x0
    MOV ACC R7
    LSL 4
    P.MAT.COL 1
    P.MAT.OPR SET_VEC
    P.MAT.COL 2
    P.MAT.OPR SET_VEC
    P.MAT.COL 3
    P.MAT.OPR SET_VEC
    
    ; Set the location of the actual transformation matrix to be SP=0x18
    ; and initialise to the identity matrix
    P.MAT.DST SP 0x18
    P.MAT.OPR IDENTITY_MAT
    
    ; Apply the prepared translation, rotation, and offset vectors
    P.MAT.SRC1 SP 0x0    ; Scale
    P.MAT.SRC2 SP 0x18
    P.MAT.DST SP 0x18
    P.MAT.OPR SCALE

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
