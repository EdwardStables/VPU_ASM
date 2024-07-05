#!/usr/bin/env python3
"""
Take in assembly file and zero or more data files and create the memory map to be loaded onto the core.

Does basic correctness checking, but nothing fancy.
"""

from argparse import ArgumentParser
from instructions import InstructionDefinition, ISADefinition
from instructions import InvalidOperandException, InvalidOpcodeException, InvalidOperandNumberException
import instructions
from pathlib import Path

class SourceLine:
    def __init__(self, file: Path, linenumber: int, source: str):
        self.file = file
        self.linenumber = linenumber
        self.source = source

    def is_instr(self):
        #Only valid to run once validate has correctly run
        return self.source.startswith("    ")
    
    def validate(self):
        index, msg = self.validate_form()
        if index is not None and msg is not None:
            return self.annotate(index=index, msg=msg)
        return None

    def validate_form(self):
        if self.source == "":
            return None, None

        if self.source.startswith("    "):
            return self.validate_instruction_form()
        
        if self.source[0] == " ":
            return 0, "Invalid whitespace, labels must have zero indentation and instructions must have 4 spaces"

        #Label
        for i, c in enumerate(self.source):
            if i == 0 and c.isdigit():
                return 0, "First digit of label cannot be an integer"
            if i == len(self.source)-1 and c != ":":
                return i, "Labels must end with a colon"
            if i < len(self.source)-1 and not c.isupper() and not c.isdigit():
                return i, "Labels can only contain integers and uppercase letters"

        return None, None 
    
    def validate_instruction_form(self):
        return None, None

    def annotate(self, index=None, operand_index=None, msg=None):
        assert not (index and operand_index), "Cannot set both index and operand_index in an annotate call"
        if operand_index is not None:
            assert self.is_instr(), "Cannot set operand_index for non-instructions"
            point = 4
            seen = 0
            last =  ""
            for i in self.source[4:]:
                if i != " " and last == " ": seen += 1
                if seen==operand_index: break
                last = i
                point += 1
                
        elif index is not None:
            point = index
        else:
            point = None        

        ret = f"{self.file}:{self.linenumber} "
        offset = len(ret)
        ret += self.source + "\n"
        if point is not None or msg is not None:
            ret += " "*offset
        
        if point is not None:
            ret += " "*point + "^"
        
        if msg is not None:
            ret += " " + msg

        return ret
            

class ProgramInstruction:
    def __init__(self, sourceline: SourceLine, isa: ISADefinition):
        self.sourceline = sourceline
        self.isa = isa
        #assume all inputs are well-formed instructions, not empty or labels
        self.ops = [i for i in self.sourceline.source.split() if i]
        self._encode()

    def _encode(self) -> bool:
        try:
            self.isa.match(self.ops[0], *self.ops[1:])
        except InvalidOpcodeException as e:
            print(self.sourceline.annotate(operand_index=0, msg=f"Unknown opcode '{self.ops[0]}'"))
        except InvalidOperandNumberException as e:
            print(self.sourceline.annotate(operand_index=1, msg=f"Invalid number of operands ({len(self.ops)-1}) for opcode {self.ops[0]}"))

class Block:
    pass

class Program:
    def __init__(self, file: Path, isa: ISADefinition):
        self.file = file
        self.source_lines: list[SourceLine] = []
        with self.file.open() as f:
            for i, line in enumerate(f):
                line = line[:line.find(";")]
                line = line.rstrip()
                sl = SourceLine(self.file, i, line)
                if msg := sl.validate():
                    print(msg)
                self.source_lines.append(sl)
        
        for sl in self.source_lines:
            if not sl.is_instr(): continue
            ProgramInstruction(sl, isa)


def get_args():
    parser = ArgumentParser()
    isa_file = "instructions.yaml"
    parser.add_argument("asm_file", type=str, help="Input program")
    parser.add_argument("--isa", type=str, default=isa_file, help=f"Path to ISA file. Defaults to {isa_file}")
    parser.add_argument("--data", type=str, nargs="+", help="Input data file(s)")
    parser.add_argument("-o", action="store_true", help="Output file name")
    return parser.parse_args()

def main():
    args = get_args()
    isa = ISADefinition(instructions.load_from_yaml(args.isa))
    program = Program(Path(args.asm_file), isa)

if __name__ == "__main__":
    main()