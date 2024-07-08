#!/usr/bin/env python3
"""
Create definitions based off yaml file input. Used as library and standalone
"""

from __future__ import annotations
from dataclasses import dataclass
from yaml import safe_load
from pathlib import Path
from enum import IntEnum

OPTYPES = ["REG","LAB","IMM","IMM16","IMM24"]
class OperandType(IntEnum):
    REG=0
    LAB=1
    IMM=2 #invalid in specification, given as general parsing type for 16/24
    IMM16=3
    IMM24=4

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
class InstructionDefinition:
    def __init__ (self, name, ops, flags, desc, encoding):
        self.name = name
        self.ops = ops
        self.flags = flags
        self.desc = desc
        self.encoding = encoding           
        self.internal_name = self.name + "_" + "_".join([OPTYPES[o][0] for o in self.ops])

    def __eq__(self, other: InstructionDefinition):
        return self.name == other.name and self.ops == other.ops

class ISADefinition:
    def __init__(self, data: dict):
        
        self.next_encoding = 0
        self.instructions: list[InstructionDefinition] = []
        self.registers: list[str] = []
        self.valid_keys = ["name", "ops", "flags", "desc"]
        self.data = data

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
        if not isinstance(self.data["instructions"], list):
            return (False, f"Expected value of 'instructions' to be a list, found {type(self.data['instructions'])}")
        if not isinstance(self.data["registers"], list):
            return (False, f"Expected value of 'registers' to be a list, found {type(self.data['registers'])}")
        
        for i, instr in enumerate(self.data["instructions"]):
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

        for i, reg in enumerate(self.data["registers"]):
            if not isinstance(reg, str):
                return (False, f"Register list entry {i}. Expected type of entry to be a str, found {type(reg)}")

        return (True,"")

    def _parse(self):
        for i, reg in enumerate(self.data["registers"]):
            if reg in self.registers:
                return (False, f"Register list entry {i} is duplicated.")
            self.registers.append(reg)
        for i, instr in enumerate(self.data["instructions"]):
            name = instr["name"]
            ops = []
            for op in instr.get("ops", []):
                if op == "REG": ops.append(OperandType.REG)
                elif op == "LAB": ops.append(OperandType.LAB)
                elif op == "IMM": 
                    return (False, f"Instruction list entry i specifies an IMM operand which is not legal.")
                elif op == "IMM16": ops.append(OperandType.IMM16)
                elif op == "IMM24": ops.append(OperandType.IMM24)

            flags = instr.get("flags", [])
            desc = instr["desc"]
            new_instr = InstructionDefinition(name, ops, flags, desc, self.next_encoding)
            if new_instr in self.instructions:
                return (False, f"Instruction list entry {i} is a duplicated definition.")
            self.instructions.append(new_instr)
            self.next_encoding += 1

        return True, ""

    def match(self, opcode_str: str, *ops) -> tuple[bool,tuple[int,str]|InstructionDefinition]:
        trial: list[InstructionDefinition] = []
        for i in self.instructions:
            if i.name == opcode_str:
                trial.append(i)
        
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
        except InvalidOperandException:
            return False, (i+1, f"Could not determine type of operand {o}")
        
        def check_equality(ref, test):
            _ref = [OperandType.IMM if i in (OperandType.IMM24,OperandType.IMM16) else i for i in ref]
            return _ref == test

        filtered_trial = [t for t in trial if check_equality(t.ops, optypes)]

        if not filtered_trial:
            found = [OPTYPES[ot] for ot in optypes]
            msg = f"Operand types do not match expected format for opcode {opcode_str}.\n"
            expected = []
            for exp in trial:
                expected.append('['+(','.join([OPTYPES[ot] for ot in exp.ops])) + ']')
            expected = " or ".join(expected)
            msg += f"Got: [{','.join(found)}]. Expected {expected}"
            return False, (1, msg)

        return True, trial[0]

    def get_operand_type(self, operand: str) -> OperandType:
        if operand in self.registers:
            return OperandType.REG
        if operand[0].isupper() and all(i.isdigit() or i.isupper() for i in operand):
            return OperandType.LAB
        if all(i.isdigit() for i in operand):
            return OperandType.IMM
        
        raise InvalidOperandException

    def get_reg_encoding(self, reg: str) -> int:
        try:
            return self.registers.index(reg)
        except ValueError:
            print(f"Internal error, tried to look up encoding of unknown register {reg}. This should not happen.")
            exit(1)
        
from jinja2 import Environment, BaseLoader
class Formatter:
    def __init__(self, instructions: ISADefinition):
        self.instructions = instructions
    
    def render_cpp(self, output_file):
        template_str = """#pragma once

enum Instructions {
{% for i in instructions %} {{i.internal_name}} = {{i.encoding}},
{% endfor %}
};

"""
        template = Environment(loader=BaseLoader).from_string(template_str) 
        data = template.render({"instructions":self.instructions.instructions})

        print(data)

    def render_table(self, output_file):

        disp_instrs = []
        headers = [" Name ", " Operands ", " Flags ", " Encoding ", " Description "]
        max_widths = [len(h) for h in headers]

        disp_instrs = []
        for i in self.instructions.instructions:
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
    parser.add_argument("--cpp", action="store_true", help="Generate C++ defs")
    parser.add_argument("--table", action="store_true", help="Generate markdown formatted table")
    args = parser.parse_args()
    
    instruction_dict = load_from_yaml(Path(args.definitions))
    
    try:
        instructions = ISADefinition(instruction_dict)
    except Exception:
        exit(1)


    formatter = Formatter(instructions)
    #if args.sv:
    #    formatter.render_sv("defs_pkg.sv")

    if args.cpp:
        formatter.render_cpp("defs_pkg.h")
    
    if args.table:
        formatter.render_table("defs.md")

if __name__ == "__main__":
    main()