# VPU ASM

Repo contains documentation and assembler for VPU assembly, as well as test programs.

Language is designed to benefit the hardware as much as possible, therefore making it a pretty bad and inexpressive ASM dialect. Assembler is python for ease of development and not really needing performance currently due to the size of test programs.

## Memory Model

Hardware currently assumes 512-bytes of addressible memory. Reset vector is 0x0, soft-limit for program size is 4kB because I wanted to pick an arbitrary small number. No reason this can't increase later.

Load-store style architecture. The core is not really intended to be doing much computation, rather to set up kicks for dedicated hardware.

## Core Configuration

Registers:
- 8 GP regs
- ACC reg
- PC
- O (overflow) flag
- C (compare) flag

ACC (accumulator) reg is the input and target of all ALU operations, as well as source and dest for memory operations.

## Instructions

### Core Instructions

Core instructions are directly executed on the CPU. All core instructions are 32-bit.

Byte 1 is the instruction, by convention bit zero is set to indicate a hardware kick and unset for a CPU instruction.

Bytes 2, 3, and 4 are operands, and can be combined for larger constants.

User instructions.py to generate a markdown table of instructions based on the yaml file, if required.

### HW Instructions

HW instructions offload operations to dedicated hardware pipelines. Hardware cores operate off control streams (semi-arbitrary instructions stored in memory). These can be pre-assembled before execution (and just pointed to by the ASM program) or can be manually assembled at runtime, but this is probably a bad idea. Therefore hardware kicks just need to run a pipeline with a control stream base address. A hardware kick instruction is non-blocking, they can run in parallel. For simplicity, only one kick of a single hardware pipeline can be in progress at any one time.

An exception to the above is the MMU, which provides several DMA operations the CPU can use without a control stream. DMA operations _are_ blocking. Additionally, the BLOCK instruction halts execution until all active kicks have finished. DMA instructions are prepended by D, and hardware kicks by H.

| Name  | Operands             | Flags | Description |
| ----- | ----------           | ----- | ----------- |
| D.CP  | REGD, REGS, REG_SIZE |       | DMA copy REG_SIZE bytes starting from the address in REGS to the address in REGD |
| D.SET | REGD, REGV, REG_SIZE |       | DMA set REG_SIZE bytes starting from the address in REGD to the value in REG_SIZE |
| H.RUN | REG_CS               |       | Run test pipeline on control stream address held in REG_CS |
| BLOCK |                      |       | Wait until the completion of all kicks has been signalled |MOV

TODO: move above table into yaml