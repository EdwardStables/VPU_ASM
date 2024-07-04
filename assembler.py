#!/usr/bin/env python3
"""
Take in assembly file and zero or more data files and create the memory map to be loaded onto the core.

Does basic correctness checking, but nothing fancy.
"""

from argparse import ArgumentParser
from instructions import Instruction, Instructions, load_from_yaml
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
        point, msg = self.validate_form()
        if point is not None and msg is not None:
            return self.annotate(point=point, msg=msg)
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

    def annotate(self, point=None, msg=None):
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
    def __init__(self, sourceline: SourceLine, instrs: Instructions):
        self.sourceline = sourceline

        #assume all inputs are well-formed instructions, not empty or labels
        ops = [i for i in self.sourceline.source.split() if i]
        print(self.sourceline.linenumber, ops)

class Block:
    pass

class Program:
    def __init__(self, file: Path, instrs: Instructions):
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
            ProgramInstruction(sl, instrs)


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
    instructions = Instructions(load_from_yaml(args.isa))
    program = Program(Path(args.asm_file), instructions)

if __name__ == "__main__":
    main()