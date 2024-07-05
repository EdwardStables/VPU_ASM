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

        ret = f"{self.file}:{self.linenumber+1} "
        offset = len(ret)
        ret += self.source + "\n"
        if point is not None or msg is not None:
            ret += " "*offset
        
        if point is not None:
            ret += " "*point + "^"
        
        if msg is not None:
            ret += " " + msg

        return ret
            
class Block:
    pass

class Program:
    def __init__(self, file: Path, isa: ISADefinition):
        self.file = file
        self.isa = isa
        self.source_lines: list[SourceLine] = []
        with self.file.open() as f:
            for i, line in enumerate(f):
                line = line[:line.find(";")]
                line = line.rstrip()
                sl = SourceLine(self.file, i, line)
                if msg := sl.validate():
                    print(msg)
                self.source_lines.append(sl)
        
        self.instructions = []
        error_count = 0
        for sl in self.source_lines:
            if not sl.is_instr(): continue
            
            #Valid is bool.
            #Encoding is 1-4 entry list. Opcode, registers, and immediates are encoded.
            #Label ref gives an index of the encoding that contains a label. 0 for none
            valid, encoding, label_ref = self.get_encoding(sl)
            
            if valid:
                self.instructions.append((sl,encoding,label_ref))
            else:
                error_count+=1

            if error_count > 5:
                print("Reached max error count, exiting.")
                exit(1)

        for sl, encoding, label_ref in self.instructions:
            print(encoding, label_ref)


        
    def get_encoding(self, sourceline):
        #assume all inputs are well-formed instructions, not empty or labels
        ops = [i for i in sourceline.source.split() if i]
        valid, result = self.isa.match(ops[0], *ops[1:])
        if not valid:
            operand_index, msg = result
            msg = sourceline.annotate(operand_index=operand_index, msg=msg)
            print(msg)
            return False, None, None

        instr_def = result
        label_index = 0
        encoding = [instr_def.encoding] 
        for i, o in enumerate(instr_def.ops):
            match o:
                case instructions.OperandType.REG:
                    encoding.append(self.isa.get_reg_encoding(ops[i+1]))
                case instructions.OperandType.IMM:
                    encoding.append(int(ops[i+1]))
                case instructions.OperandType.LAB:
                    encoding.append(ops[i+1])
                    label_index = i+1
        return True, encoding, label_index

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
    try:
        isa = ISADefinition(instructions.load_from_yaml(args.isa))
    except instructions.InstructionFormatException:
        print("Badly formed ISA file, exiting.")
        exit(1)
    program = Program(Path(args.asm_file), isa)

if __name__ == "__main__":
    main()