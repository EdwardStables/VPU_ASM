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
                comment = line.find(";")
                if comment != -1:
                    line = line[:line.find(";")]
                line = line.rstrip()
                sl = SourceLine(self.file, i, line)
                if msg := sl.validate():
                    print(msg)
                if sl.source:
                    self.source_lines.append(sl)
        
        self.instructions = []
        error_count = 0
        next_label_name = None
        self.label_store = {}
        for sl in self.source_lines:
            if not sl.is_instr():
                next_label_name = sl.source[:-1] #hacky, but should be validated to this form already
                if next_label_name in self.label_store:
                    error_count+=1
                    print(sl.annotate(index=0, msg=f"Invalid reuse of a label '{next_label_name}'"))
                continue
            
            #Valid is bool.
            #Encoding is 1-4 entry list. Each entry is (value, bitwidth). Opcode, registers, and immediates are encoded.
            #Label ref gives an index of the encoding that contains a label. 0 for none
            valid, encoding, label_ref = self.get_encoding(sl)
            
            if valid:
                if next_label_name:
                    self.label_store[next_label_name] = len(self.instructions)
                self.instructions.append((next_label_name,sl,encoding,label_ref))
                next_label_name = None
            else:
                error_count+=1

            if error_count > 5:
                print("Reached max error count, exiting.")
                exit(1)


        for label_name, sl, encoding, label_ref in self.instructions:
            if label_ref and encoding[label_ref][0] not in self.label_store:
                print(sl.annotate(operand_index=label_ref, msg=f"Label {encoding[label_ref][0]} is used, but not defined anywhere in the program."))
                error_count += 1
            elif label_ref:
                #mult by 4 to account for alignment
                encoding[label_ref] = (4*self.label_store[encoding[label_ref][0]],encoding[label_ref][1])

        if error_count:
            print("Encoding generation completed with errors, exiting.")
            exit(1)

        #At this point we have confidence all instructions are well-formed and all labels are valid
        self.output = []
        for label_name, sl, encoding, label_ref in self.instructions:
            val = 0
            total_width = 0
            for (value, width) in encoding[::-1]:
                val |= value << total_width
                total_width += width
            assert total_width == 32, f"{sl.file}:{sl.linenumber+1} Got total width of {total_width}"
            self.output.append(val)

        #Program region marker
        self.output.append(0xFFFFFFFF)
        
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
        encoding = [(instr_def.encoding,8)] 
        for i, o in enumerate(instr_def.ops):
            match o:
                case instructions.OperandType.REG:
                    encoding.append((self.isa.get_reg_encoding(ops[i+1]),8))
                case instructions.OperandType.LAB:
                    encoding.append((ops[i+1],24)) #Labels are always 24 bits
                    label_index = i+1
                case instructions.OperandType.IMM16:
                    value = int(ops[i+1])
                    width = 16
                    if value >= 2**width:
                        msg = f"Literal value {value} is too big for 16-bit literal."
                        msg = sourceline.annotate(operand_index=operand_index, msg=msg)
                        print(msg)
                        return False, None, None
                    encoding.append((value,width))
                case instructions.OperandType.IMM24:
                    value = int(ops[i+1])
                    width = 24
                    if value >= 2**width:
                        msg = f"Literal value {value} is too big for 24-bit literal."
                        msg = sourceline.annotate(operand_index=operand_index, msg=msg)
                        print(msg)
                        return False, None, None
                    encoding.append((value,width))
                case _:
                    assert False, "Unexpected operand value"

        #Required for standalone instructions
        if not instr_def.ops:
            encoding.append((0,24))
        if instr_def.ops == [instructions.OperandType.REG,instructions.OperandType.REG]:
            encoding.append((0,8))

        return True, encoding, label_index

def get_args():
    parser = ArgumentParser()
    isa_file = "instructions.yaml"
    parser.add_argument("asm_file", type=str, help="Input program")
    parser.add_argument("--isa", type=str, default=isa_file, help=f"Path to ISA file. Defaults to {isa_file}")
    parser.add_argument("--data", type=str, nargs="+", help="Input data file(s)")
    parser.add_argument("--output", "-o", type=str, help="Output file name", default="vpu.out")
    return parser.parse_args()

def main():
    args = get_args()
    try:
        isa = ISADefinition(instructions.load_from_yaml(args.isa))
    except instructions.InstructionFormatException:
        print("Badly formed ISA file, exiting.")
        exit(1)
    program = Program(Path(args.asm_file), isa)

    with open(args.output, "wb") as f:
        for instr in program.output:
            f.write(instr.to_bytes(4,'little'))

if __name__ == "__main__":
    main()