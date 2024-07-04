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
            

class Instruction:
    pass

class Block:
    pass

class Program:
    def __init__(self, file: Path):
        self.file = file
        self.source_lines: list[SourceLine] = []
        with self.file.open() as f:
            for i, line in enumerate(f):
                self.source_lines.append(SourceLine(self.file, i, line.rstrip()))

        for line in self.source_lines:
            print(line.source)

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
    program = Program(Path(args.asm_file))

    print()
    print(program.source_lines[0].annotate(point=4, msg="test"))


if __name__ == "__main__":
    main()