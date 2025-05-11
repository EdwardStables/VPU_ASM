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
from math import ceil

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
            if i < len(self.source)-1 and not c.isupper() and not c.isdigit() and not c == "_":
                return i, "Labels can only contain integers, underscores, and uppercase letters"

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
            
class Data:
    def __init__(self, path: Path):
        if not path.exists():
            print(f"Blob path {path} can't be found")
            exit(1)
        if path.is_dir():
            print(f"Blob path {path} is a directory, not a file")
            exit(1)

        with path.open("rb") as f:
            self.data = f.read()

    def aligned_bytes(self):
        return 4 * ceil(len(self.data) / 4)

    def as_words(self):
        ind = 0
        while True:
            if (ind >= len(self.data)): break
            out = 0
            out |= (0 if ind >= len(self.data) else int(self.data[ind])) << 0
            ind += 1
            out |= (0 if ind >= len(self.data) else int(self.data[ind])) << 8
            ind += 1
            out |= (0 if ind >= len(self.data) else int(self.data[ind])) << 16
            ind += 1
            out |= (0 if ind >= len(self.data) else int(self.data[ind])) << 24
            ind += 1
            yield out



class Program:
    def __init__(self, file: Path, isa: ISADefinition, blobs: list[Data]):
        self.file = file
        self.isa = isa
        self.blobs = blobs
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
        self.literal_ints = {}
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

        SEPARATOR_SIZE = 4
        SEPARATOR = (0xFFFFFFFF, -1)

        RESET_VECTOR = 0 #contains pointer to program start
        LITERAL_TABLE = SEPARATOR_SIZE + 4 #contains all literals
        BLOB_TABLE =    SEPARATOR_SIZE + LITERAL_TABLE + (4*len(self.literal_ints)) #one address for each blob store
        BLOB_STORE =    SEPARATOR_SIZE + BLOB_TABLE + (4*len(self.blobs))
        PROGRAM_START = SEPARATOR_SIZE + BLOB_STORE + sum(b.aligned_bytes() for b in self.blobs) 


        for i,(nln,sl,encoding,ref) in enumerate(self.instructions):
            new_encoding = []
            for op,width,blob_offset in encoding:
                new_code = (op+BLOB_TABLE) if blob_offset else op
                new_encoding.append((new_code,width))
            self.instructions[i] = (nln,sl,new_encoding,ref)

        for label_name, sl, encoding, label_ref in self.instructions:
            if label_ref and encoding[label_ref][0] not in self.label_store:
                print(sl.annotate(operand_index=label_ref, msg=f"Label {encoding[label_ref][0]} is used, but not defined anywhere in the program."))
                error_count += 1
            elif label_ref:
                #mult by 4 to account for alignment
                encoding[label_ref] = (4*self.label_store[encoding[label_ref][0]] + PROGRAM_START,encoding[label_ref][1])

        if error_count:
            print("Encoding generation completed with errors, exiting.")
            exit(1)

        #At this point we have confidence all instructions are well-formed and all labels are valid
        self.output = []
        # reset vector
        self.output.append((PROGRAM_START,-1)) 
        self.output.append(SEPARATOR) 

        # constant table
        for i, (value, index) in enumerate(self.literal_ints.items()):
            assert i == index, "Expected in-order iteration over literal dict"
            self.output.append((value,-1))

        self.output.append(SEPARATOR) 

        # blob table
        blob_offset = 0
        for blob in self.blobs:
            self.output.append((BLOB_STORE + blob_offset, -1))
            blob_offset += blob.aligned_bytes()

        self.output.append(SEPARATOR) 

        # blobs
        for blob in self.blobs:
            for word in blob.as_words():
                self.output.append((word, -1))

        self.output.append(SEPARATOR) 

        assert PROGRAM_START == len(self.output)*4, f"Mismatch between expected program start and output vector length, {PROGRAM_START} vs {len(self.output)*4}"
        
        # program
        for label_name, sl, encoding, label_ref in self.instructions:
            val = 0
            total_width = 0
            for (value, width) in encoding[::-1]:
                mask = 0
                for i in range(width):
                    mask |= 1 << i
                val |= (value & mask) << total_width
                total_width += width
            assert total_width == 32, f"{sl.file}:{sl.linenumber+1} Got total width of {total_width}"
            self.output.append((val,sl.linenumber))

        self.output.append(SEPARATOR) 
 
    def get_encoding(self, sourceline):
        #assume all inputs are well-formed instructions, not empty or labels
        instr = [i for i in sourceline.source.split() if i]
        code = instr[0]
        ops = instr[1:]
        valid, result, ops = self.isa.match(code, *ops)
        if not valid:
            operand_index, msg = result
            msg = sourceline.annotate(operand_index=operand_index, msg=msg)
            print(msg)
            return False, None, None

        def imm_to_int(imm):
            if len(imm) >= 3 and imm[0:2] == "0x" and (i.isdigit() for i in imm[2:]):
                return int(imm, base=16)
            return int(imm)

        instr_def = result
        label_index = 0
        encoding = [(instr_def.encoding,8,False)] 
        for i, o in enumerate(instr_def.ops):
            match o:
                case instructions.OperandType.REG:
                    encoding.append((self.isa.get_reg_encoding(ops[i]),8,False))
                case instructions.OperandType.LAB:
                    encoding.append((ops[i],24,False)) #Labels are always 24 bits
                    label_index = i+1
                case instructions.OperandType.BLOB_LAB:
                    index = int(ops[i][6:])
                    if index >= len(self.blobs):
                        msg = "Data blob index greater than number of provided blobs"
                        msg = sourceline.annotate(operand_index=i+1, msg=msg)
                        print(msg)
                        return False, None, None
                    encoding.append((index,16,True)) #Blob labels are indexes into the data table, note that they need offset
                case instructions.OperandType.IMM_INT:
                    value = imm_to_int(ops[i])
                    if value >= 2**32:
                        msg = f"Literal value {value} is too big for 32 bit integers"
                        msg = sourceline.annotate(operand_index=i+1, msg=msg)
                        print(msg)
                        return False, None, None
                    literal_index = self.add_literal_int(value)

                    #fill up remaining space
                    width = 24 if instr_def.ops == [instructions.OperandType.IMM_INT] else 16
                    encoding.append((literal_index,width,False))
                case _:
                    assert False, "Unexpected operand value"

        #Required for standalone instructions
        if not instr_def.ops:
            encoding.append((0,24,False))
        if instr_def.ops == [instructions.OperandType.REG]:
            encoding.append((0,16,False))
        if instr_def.ops == [instructions.OperandType.REG,instructions.OperandType.REG]:
            encoding.append((0,8,False))

        return True, encoding, label_index

    def add_literal_int(self, value: int):
        if value not in self.literal_ints:
            self.literal_ints[value] = len(self.literal_ints)
        return self.literal_ints[value]

    def write_array(self) -> list[int]:
        arr = []
        addr = 0
        for instr, line in self.output:
            if instr < 0:
                instr += (2**32)
            addr += 4
            arr.append(instr)
            assert addr < 0x100000, "Read only segment overlaps into expected writable memory region"

        return arr

    def write_out(self, path: Path, write_debug: bool):
        with path.open("wb") as f:
            addr = 0
            for instr, line in self.output:
                if instr < 0:
                    instr += (2**32)
                addr += 4
                f.write(instr.to_bytes(4,'little'))
                assert addr < 0x100000, "Read only segment overlaps into expected writable memory region"

        if write_debug:
            self.write_out_debug(path)

    def write_out_debug(self, path: Path):
        """
        Debug file:
            Fields are a 4 byte length value followed by content
            Fields are currently:
            - object file hash
            - absolute path to input file
            - line numbers corresponding to their PC offset

        This has had zero thought at space optimisation, currently not necessary
        """

        debug_path = path.parent / (path.name + ".dbg")
        with debug_path.open("wb") as f:
            # File hash
            from hashlib import md5
            with path.open('rb') as bf:
                hash = md5(bf.read())
            f.write((hash.digest_size).to_bytes(4,'little'))
            f.write(hash.digest())

            # Input file path
            encoded_path = str(self.file.absolute()).encode() 
            f.write(len(encoded_path).to_bytes(4,'little'))
            f.write(encoded_path)
            
            # Source code mapping
            f.write((len(self.output)*4).to_bytes(4,'little'))
            for instr, line in self.output:
                val = line if line != -1 else 0xFFFFFFFF
                f.write(val.to_bytes(4,'little'))



def get_args():
    parser = ArgumentParser()
    isa_file = "instructions.yaml"
    parser.add_argument("asm_file", type=str, help="Input program")
    parser.add_argument("--isa", type=str, default=isa_file, help=f"Path to ISA file. Defaults to {isa_file}")
    parser.add_argument("--data", type=str, nargs="+", help="Input data file(s)", default=[])
    parser.add_argument("--output", "-o", type=str, help="Output file name", default="vpu.out")
    parser.add_argument("--debug", "-d", action="store_true", help="Generate debug file alongside output object")
    return parser.parse_args()


def main():
    args = get_args()
    try:
        isa = ISADefinition(instructions.load_from_yaml(args.isa))
    except instructions.InstructionFormatException:
        print("Badly formed ISA file, exiting.")
        exit(1)

    in_file = Path(args.asm_file)
    if not in_file.exists():
        print("Cannot find input file", in_file)
        exit(1)

    blobs = [Data(Path(p)) for p in args.data]
    program = Program(Path(args.asm_file), isa, blobs)
    program.write_out(Path(args.output), args.debug)

if __name__ == "__main__":
    main()