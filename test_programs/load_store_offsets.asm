                        ; Write 1-10 to stack region, then accumulate the values by reading them back
    MOV R1 36           ; limit value
    MOV R3 0            ; Offset value
    MOV ACC 1           ; Save value
STORE_LOOP:
    STW SP R3           ; Save ACC to SP + R3
    CMP R3 R1           ; Have we reached the limit
    BRA SUM
    
    ADD 1               ; Increment save value
    MOV R4 ACC          ; Temp storage

    MOV ACC R3          ; Increment address offset
    ADD 4
    MOV R3 ACC

    MOV ACC R4
    JMP STORE_LOOP

SUM:
    MOV R2 0            ; Accumuation value
    MOV R3 0            ; Offset value
SUM_LOOP:
    LDW SP R3           ; Load offseted address
    ADD R2
    MOV R2 ACC          ; Update accumulation

    CMP R3 R1           ; End loop when complete
    BRA END

    MOV ACC R3         ; Update offset
    ADD 4
    MOV R3 ACC
    JMP SUM_LOOP

END:
    HLT

