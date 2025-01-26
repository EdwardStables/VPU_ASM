#!/usr/bin/env python3
"""
Create definitions based off yaml file input. Used as library and standalone
"""

from __future__ import annotations
from dataclasses import dataclass
from yaml import safe_load
from pathlib import Path
from enum import IntEnum
from PIL import Image
from hashlib import md5

OPTYPES = ["REG","LAB","IMM_INT","BLOB_LAB"]

class FontGenerator:
    def __init__(self, path: Path):
        self.path = path 
        self.glyph_size = 8 #8x8 pixels
        self.glyph_count = 96 #number of symbols. Base ascii from 32-127 inclusive
        self.table = []

    def load(self):
        image = Image.open(self.path)
        pixels = image.load()

        if image.size[0] % self.glyph_size != 0:
            raise Exception(f"Font image width not a multiple of {self.glyph_size}")
        if image.size[1] % self.glyph_size != 0:
            raise Exception(f"Font image height not a multiple of {self.glyph_size}")

        x_count = int(image.size[0]/self.glyph_size)
        y_count = int(image.size[1]/self.glyph_size)
        total_count = x_count * y_count

        if total_count != self.glyph_count:
            raise Exception(f"Found a total of {total_count} glyphs, but expected {self.glyph_count}")

        for y in range(y_count):
            ypos = y*self.glyph_size
            for x in range(x_count):
                xpos = x*self.glyph_size

                glyph_val = 0
                line_val = 0
                for line in range(self.glyph_size):
                    for col in range(self.glyph_size):
                        pixel = pixels[xpos + col, ypos + line]
                        if pixel[3] != 0: #if not blank
                            line_val |= (1<<((self.glyph_size-1)-col))
                    glyph_val |= (line_val<<(self.glyph_size*((self.glyph_size-1)-line)))
                    line_val = 0
                self.table.append(glyph_val)

    def get_values(self):
        return [hex(v) for v in self.table]

class OperandType(IntEnum):
    REG=0
    LAB=1
    IMM_INT=2
    BLOB_LAB=3

def load_from_yaml(path: str|Path) -> dict:
    if isinstance(path, str):
        path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Yaml file {path} cannot be found")

    with path.open() as f:
        data = safe_load(f)

    return data

class InstructionFormatException(Exception): pass
class InvalidOpcodeException(InstructionFormatException): pass
class InvalidOperandException(InstructionFormatException): pass
class InvalidOperandNumberException(InvalidOperandException): pass
class IllegalRegisterException(InvalidOperandException): pass
class InstructionDefinition:
    def __init__ (self, name, ops, flags, desc, encoding):
        self.name = name
        self.ops = ops
        self.flags = flags
        self.desc = desc
        self.encoding = encoding           
        self.internal_name: str = self.name
        if self.ops: 
            self.internal_name += "_" + "_".join([OPTYPES[o][0] for o in self.ops])
        self.internal_name = self.internal_name.replace(".","_")

    def __eq__(self, other: InstructionDefinition):
        return self.name == other.name and self.ops == other.ops

class InstructionArray:
    def __init__(self, data: list, initial_encoding: int):
        self.data = data 
        self.instructions: list[InstructionDefinition] = []
        self.next_encoding = initial_encoding
        self.valid_keys = ["name", "ops", "flags", "desc"]
        self.prefix = []

    def set_prefix(self, prefix: str|list[str]):
        if isinstance(prefix, str):
            prefix = [prefix]
        self.prefix = prefix

    def validate(self):
        for i, instr in enumerate(self.data):
            if not isinstance(instr, dict):
                return (False, f"Instruction list entry {i}. Expected type of entry to be a dict, found {type(instr)}")
            for k, v in instr.items():
                if k not in self.valid_keys:
                    return (False, f"Instruction list entry {i}. Found invalid key '{k}'")
            if "name" not in instr:
                return (False, f"Instruction list entry {i}. Missing required key 'name'")
            if "desc" not in instr:
                return (False, f"Instruction list entry {i}. Missing required key 'desc'")
            if "ops" in instr:
                if not isinstance(instr["ops"], list):
                    return (False, f"Instruction list entry {i}. Value of ops must be a list")
                for op_ind, op in enumerate(instr["ops"]):
                    if op not in OPTYPES:
                        return (False, f"Instruction list entry {i}, op entry {op_ind}. {op} is not a valid operand type")
        
        return True, ""
    
    def parse(self, flag_defs):
        if self.prefix:
            prefix = ".".join(self.prefix) + "."
        else:
            prefix = ""

        for i, instr in enumerate(self.data):
            name = prefix + instr["name"]
            ops = []
            for op in instr.get("ops", []):
                if op == "REG": ops.append(OperandType.REG)
                elif op == "LAB": ops.append(OperandType.LAB)
                elif op == "IMM_INT": ops.append(OperandType.IMM_INT)
                elif op == "BLOB_LAB": ops.append(OperandType.BLOB_LAB)

            flags = instr.get("flags", [])
            for f in flags:
                if f not in flag_defs:
                    return (False, f"Instruction list entry {i} uses unknown flag {f}.")

            desc = instr["desc"]
            new_instr = InstructionDefinition(name, ops, flags, desc, self.next_encoding)
            if new_instr in self.instructions:
                return (False, f"Instruction list entry {i} is a duplicated definition.")
            self.instructions.append(new_instr)
            self.next_encoding += 1
        return True, ""

    def instr_gen(self):
        for i in self.instructions:
            yield i

class Pipe:
    def __init__(self, data: dict, initial_encoding: int):
        self.data: dict = data
        self.name: str = None 
        self.prefix: str = None
        self.instructions: InstructionArray = None
        assert initial_encoding >= 128, "Expected pipeline instr to have MSB set"
        self.next_encoding = initial_encoding
        self.encoding_prefix = initial_encoding >> 4
        self.aliases = {}

    def validate(self):
        if "name" not in self.data.keys():
            return (False, f"Could not find top level pipe key 'name'")
        if "prefix" not in self.data.keys():
            return (False, f"Could not find top level pipe key 'prefix'")
        if "instructions" not in self.data.keys():
            return (False, f"Could not find top level pipe key 'instructions'")
        if "alias" in self.data.keys():
            a = self.data["alias"]
            if type(a) != dict:
                return (False, f"Alias field unexpected type: {type(a)}. Expected dict.")
            for key, value in a.items():
                if type(value) != list:
                    return (False, f"Alias field {value} value is unexpected type: {type(value)}. Expected list.")
                for v in value:
                    if type(v) != str:
                        return (False, f"Alias entry {v} is unexpected type: {type(v)}. Expected str.")


        self.instructions = InstructionArray(self.data["instructions"], self.next_encoding)
        valid, err = self.instructions.validate()
        if not valid:
            return False, err

        return (True,"")

    def parse(self, isa: ISADefinition):
        self.name = self.data["name"]
        self.prefix = self.data["prefix"]

        self.instructions.set_prefix(["P", self.prefix])
        valid, err = self.instructions.parse(isa.flags)
        if not valid:
            return False, err

        if "alias" in self.data.keys():
            for _, value in self.data["alias"].items():
                for i, v in enumerate(value):
                    self.aliases[v] = i

        assert len(self.instructions.instructions) <= 16, "Cannot have more than 16 instructions per hardware pipe"
        self.next_encoding = self.instructions.next_encoding
        return True, ""

#Read-only data included inside the build
class Data:
    def __init__(self, asm_root: Path):
        self.font = FontGenerator(asm_root/"ascii_sheet.png")
        self.font.load()

class ISADefinition:
    def __init__(self, data: dict):
        
        self.next_encoding = 0
        self.instructions: InstructionArray = None
        self.flags: list[str] = []
        self.registers: list[str] = []
        self.data = data
        self.pipes: list[Pipe] = []
        self.memory_size = None
        self.memory_width = None

        valid, msg = self._validate_data()
        if not valid:
            print("Error:", msg)
            raise Exception("Invalid input file")

        valid, msg = self._parse()
        if not valid:
            print("Error:", msg)
            raise Exception("Invalid input file")

    def _validate_data(self) -> tuple[bool,str]:
        """
        Validate the form of the data, does not do semantic checking
        """
        if "instructions" not in self.data.keys():
            return (False, f"Could not find top level key 'instructions'")
        if "registers" not in self.data.keys():
            return (False, f"Could not find top level key 'registers'")
        if "flags" not in self.data.keys():
            return (False, f"Could not find top level key 'flags'")
        if "memory" not in self.data.keys():
            return (False, f"Could not find top level key 'memory'")

        if not isinstance(self.data["registers"], list):
            return (False, f"Expected value of 'registers' to be a list, found {type(self.data['registers'])}")
        if not isinstance(self.data["flags"], list):
            return (False, f"Expected value of 'flags' to be a list, found {type(self.data['flags'])}")
        if not isinstance(self.data["instructions"], list):
            return (False, f"Expected value of 'instructions' to be a list, found {type(self.data['instructions'])}")
        if not isinstance(self.data["memory"], dict):
            return (False, f"Expected value of 'memory' to be a dict, found {type(self.data['memory'])}")

        for i, reg in enumerate(self.data["registers"]):
            if not isinstance(reg, str):
                return (False, f"Register list entry {i}. Expected type of entry to be a str, found {type(reg)}")
        for i, flag in enumerate(self.data["flags"]):
            if not isinstance(flag, dict):
                return (False, f"Flag list entry {i}. Expected type of entry to be a dict, found {type(flag)}")
            if "flag" not in flag:
                return (False, f"Flag list entry {i}. Missing required key 'flag'")
            if "name" not in flag:
                return (False, f"Flag list entry {i}. Missing required key 'name'")
        for k, v in self.data["memory"].items():
            if not isinstance(k, str):
                return (False, f"Memory entry {k}. Expected type of key to be a str, found {type(k)}")
            if not isinstance(v, int):
                return (False, f"Memory entry {k}. Expected type of value to be an int, found {type(v)}")
        if set(self.data["memory"].keys()) != set(["size", "width"]):
            return (False, f"Error in memory specification, expected only keys 'size' and 'width'.")


        self.instructions = InstructionArray(self.data["instructions"], 0)
        valid, err = self.instructions.validate()
        if not valid:
            return False, err

        next_pipe_encoding = 128
        if "pipes" in self.data.keys():
            if not isinstance(self.data["pipes"], list):
                return (False, f"Expected value of 'pipes' to be a list, found {type(self.data['pipes'])}")
            for i, pipe in enumerate(self.data["pipes"]):
                new_pipe = Pipe(pipe, next_pipe_encoding)
                valid, err = new_pipe.validate()
                if not valid:
                    return False, err
                assert new_pipe.next_encoding < next_pipe_encoding + 16, "Next encoding incremented more than expected"
                next_pipe_encoding += 16
                self.pipes.append(new_pipe) 


        return (True,"")

    def _parse(self):
        for i, reg in enumerate(self.data["registers"]):
            if reg in self.registers:
                return (False, f"Register list entry {i} is duplicated.")
            self.registers.append(reg)
        for i, flag in enumerate(self.data["flags"]):
            flag = flag["flag"]
            if flag in self.flags:
                return (False, f"Flag list entry {i} is duplicated.")
            self.flags.append(flag)
        self.memory_size = self.data["memory"]["size"]
        self.memory_width = self.data["memory"]["width"]

        valid, err = self.instructions.parse(self.flags)
        if not valid:
            return False, err

        for i,  pipe in enumerate(self.pipes):
            valid, err = pipe.parse(self)
            if not valid:
                return False, err

        return True, ""

    def match(self, opcode_str: str, *ops) -> tuple[bool,tuple[int,str]|InstructionDefinition]:
        trial: list[InstructionDefinition] = []
        aliases: dict[str,str] = {}
        for i, pipe in self.all_instructions_and_pipes():
            if i.name == opcode_str:
                trial.append(i)
                
                #Expect to only see one pipe for a matching instr, therefore only one set of aliases
                if pipe is not None:
                    aliases = pipe.aliases
        
        ops = tuple(o if o not in aliases else str(aliases[o]) for o in ops)
        
        if not trial:
            return False, (0, f"Unknown opcode '{opcode_str}'")

        filtered_trial = [t for t in trial if len(t.ops) == len(ops)]

        if not filtered_trial:
            return False, (1, f"Invalid number of operands ({len(ops)}) for opcode {opcode_str}.")
        trial = filtered_trial


        try:
            optypes = []
            for i, o in enumerate(ops):
                optypes.append(self.get_operand_type(o))
        except IllegalRegisterException:
            return False, (i+1, f"Register {o} is valid, but cannot be used in this context")
        except InvalidOperandException:
            return False, (i+1, f"Could not determine type of operand {o}")
        
        filtered_trial = [t for t in trial if (t.ops == optypes)]

        if not filtered_trial:
            found = [OPTYPES[ot] for ot in optypes]
            msg = f"Operand types do not match expected format for opcode {opcode_str}.\n"
            expected = []
            for exp in trial:
                expected.append('['+(','.join([OPTYPES[ot] for ot in exp.ops])) + ']')
            expected = " or ".join(expected)
            msg += f"Got: [{','.join(found)}]. Expected {expected}"
            return False, (1, msg), ops

        return True, filtered_trial[0], ops

    def get_operand_type(self, operand: str) -> OperandType:
        if operand in self.registers:
       #     if operand in ["PC", "RA", "SP"]:
       #         raise IllegalRegisterException
            return OperandType.REG
        if operand[0].isupper() and all(i.isdigit() or i.isupper() or i == "_" for i in operand):
            return OperandType.LAB
        if operand.startswith(".DATA.") and all(i.isdigit() for i in operand[6:]):
            return OperandType.BLOB_LAB
        if operand[0].isdigit() or (len(operand) > 1 and operand[0] == "-"):
            negative = operand[0] == "-"
            val = operand if not negative else operand[1:]
            if all(i.isdigit() for i in val) or\
                len(val) >= 3 and val[0:2] == "0x" and (i.isdigit() for i in val[2:]):
                return OperandType.IMM_INT
        
        raise InvalidOperandException

    def get_reg_encoding(self, reg: str) -> int:
        try:
            return self.registers.index(reg)
        except ValueError:
            print(f"Internal error, tried to look up encoding of unknown register {reg}. This should not happen.")
            exit(1)

    def all_instructions(self):
        for i in self.instructions.instr_gen():
            yield i
        for p in self.pipes:
            for i in p.instructions.instr_gen():
                yield i

    def all_instructions_and_pipes(self):
        for i in self.instructions.instr_gen():
            yield i, None
        for p in self.pipes:
            for i in p.instructions.instr_gen():
                yield i, p

        
from jinja2 import Environment, FileSystemLoader
class Formatter:
    def __init__(self, isa: ISADefinition, data: Data, template_path: Path, force_generate: bool):
        self.isa = isa
        self.data = data
        self.template_path = template_path
        self.force_generate = force_generate

    def check_hash(self, file, hashfile):
        if file.exists() and hashfile.exists():
            with file.open() as f:
                current_hash = int.from_bytes(md5(f.read().encode("utf-8")).digest(), "big")
            with hashfile.open() as f:
                saved_hash = int(f.read(), base=16)

            if current_hash != saved_hash:
                if not self.force_generate:
                    print(f"Detected change to generated file {file}. Please make sure any changes are replicated in the template. Override this warning with --force.")
                    exit(1)
                else:
                    print(f"Detected change to generated file {file}. --force is set so overwriting changes")

    
    def render_cpp(self, output_file, namespace):
        cpp_file = output_file + ".cpp"
        header_file = output_file + ".h"
        cpp_hash_file = cpp_file + ".md5"
        header_hash_file = header_file + ".md5"
        cpp_file = Path(cpp_file)
        cpp_hash_file = Path(cpp_hash_file)
        header_file = Path(header_file)
        header_hash_file = Path(header_hash_file)

        self.check_hash(cpp_file, cpp_hash_file)
        self.check_hash(header_file, header_hash_file)

        warning = """
//************************************************//
//WARNING: THIS FILE IS AUTOGENERATED, DO NOT EDIT//
//************************************************//
"""        

        header_template = Environment(loader=FileSystemLoader(self.template_path)).get_template("cpp_def.h.j2")
        header_data = header_template.render({
            "warning": warning,
            "namespace": namespace,
            "instructions": [i for i in self.isa.all_instructions()],
            "max_opcode_len": max([len(i.internal_name) for i in self.isa.all_instructions()]),
            "registers": self.isa.registers,
            "flags": self.isa.flags,
            "pipes": self.isa.pipes,
            "mem_size_mb": self.isa.memory_size,
            "mem_access_width_bytes": self.isa.memory_width,
            "ascii_glyphs": self.data.font.get_values(),
        })

        imp_template = Environment(loader=FileSystemLoader(self.template_path)).get_template("cpp_def.cpp.j2")
        imp_data = imp_template.render({
            "warning": warning,
            "namespace": namespace,
            "header": Path(output_file).stem,
            "instructions": [i for i in self.isa.all_instructions()],
            "registers": self.isa.registers,
            "flags": self.isa.flags,
        })

        with header_file.open("w") as f:
            f.write(header_data)
        with header_hash_file.open("w") as f:
            f.write(hex(int.from_bytes(md5(header_data.encode("utf-8")).digest(), "big"))[2:])
        with cpp_file.open("w") as f:
            f.write(imp_data)
        with cpp_hash_file.open("w") as f:
            f.write(hex(int.from_bytes(md5(imp_data.encode("utf-8")).digest(), "big"))[2:])

    def render_table(self, output_file):
        disp_instrs = []
        headers = [" Name ", " Operands ", " Flags ", " Encoding ", " Description "]
        max_widths = [len(h) for h in headers]

        disp_instrs = []
        for i in self.isa.all_instructions():
            line = [i.name, ','.join([OPTYPES[o] for o in i.ops]), ",".join(i.flags), hex(i.encoding), i.desc]
            line = [" "+c+" " for c in line]
            disp_instrs.append(line) 
        
        for line in disp_instrs:
            for i,l in enumerate(line):
                max_widths[i] = max(max_widths[i],len(l))

        for line in disp_instrs:
            for i,l in enumerate(line):
                l = l + " "*(max_widths[i]-len(l))
                line[i] = l

        for i,h in enumerate(headers):
            h = h + " "*(max_widths[i]-len(h))
            headers[i] = h    


        data = "|" + "|".join(headers) + "|\n"
        sep = ["-"*len(h) for h in headers]
        data += "|" + "|".join(sep) + "|\n"
        for i in disp_instrs:
            data += "|" + "|".join(i) + "|\n"

        print(data)

from argparse import ArgumentParser
def main():
    parser = ArgumentParser()
    parser.add_argument("definitions", type=str, help="YAML file with instruction definitions")
    parser.add_argument("--sv", action="store_true", help="Generate SystemVerilog defs")
    parser.add_argument("--cpp", nargs="?", const="defs_pkg", help="Generate C++ defs")
    parser.add_argument("--namespace", type=str, default="vpu::defs", help="C++ namespace to use. Defaults to vpu::defs")
    parser.add_argument("--table", action="store_true", help="Generate markdown formatted table")
    parser.add_argument("--templates", type=str, help="Give path to templates directory")
    parser.add_argument("--force", action="store_true", help="Force cpp/header files to be generated even if there are manual changes detected in the output files which will be overwritten")
    args = parser.parse_args()
    
    instruction_dict = load_from_yaml(Path(args.definitions))
    
    try:
        instructions = ISADefinition(instruction_dict)
    except Exception as e:
        print(f"Hit unexpected exception when reading instruction yaml:\n{e}")
        raise

    try:
        data = Data(Path(args.definitions).parent)
    except Exception as e:
        print(f"Hit unexpected exception when generating build-time data:\n{e}")
        raise


    if not args.templates:
        templates = Path(__file__).parent.resolve()/"templates"
    else:
        templates = Path(args.templates)

    if not templates.exists():
        print(f"Could not find templates directory {templates}")
        exit(1)
    if not templates.is_dir():
        print(f"Templates path {templates} exists but is not directory ")
        exit(1)

    formatter = Formatter(instructions, data, templates, args.force)
    #if args.sv:
    #    formatter.render_sv("defs_pkg.sv")

    if args.cpp:
        formatter.render_cpp(args.cpp, args.namespace)
    
    if args.table:
        formatter.render_table("defs.md")

if __name__ == "__main__":
    main()