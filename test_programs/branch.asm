    MOV 0
    MOV R1 10
LOOP:
    ADD 1
    CMP ACC R1
    BRA END
    JMP LOOP 
END:
    HLT