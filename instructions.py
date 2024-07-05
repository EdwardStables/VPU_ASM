#!/usr/bin/env python3
"""
Create definitions based off yaml file input. Used as library and standalone
"""

from yaml import safe_load
from pathlib import Path

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
        self.internal_name = self.name + "_" + "_".join([o[0] for o in self.ops])

class ISADefinition:
    def __init__(self, data: dict):
        
        self.next_encoding = 0
        self.instructions: list[InstructionDefinition] = []
        self.valid_keys = ["name", "ops", "flags", "desc"]
        self.data = data

        valid, msg = self._validate_data()
        if not valid:
            print(msg)
            raise Exception("Invalid input file")

        self._parse()

    def _validate_data(self) -> tuple[bool,str]:
        """
        Validate the form of the data, does not do semantic checking
        """
        if list(self.data.keys())[0] != "instructions":
            return (False, f"Top level key was expected to be 'instructions', found {list(self.data.keys())[0]}")
        if not isinstance(self.data["instructions"], list):
            return (False, f"Expected value of 'instructions' to be a list, found {type(self.data['instructions'])}")
        
        for i, instr in enumerate(self.data["instructions"]):
            if not isinstance(instr, dict):
                return (False, f"List entry {i}. Expected type of entry to be a dict, found {type(instr)}")
            for k, v in instr.items():
                if k not in self.valid_keys:
                    return (False, f"List entry {i}. Found invalid key '{k}'")
            if "name" not in instr:
                return (False, f"List entry {i}. Missing required key 'name'")
            if "desc" not in instr:
                return (False, f"List entry {i}. Missing required key 'desc'")

        return (True,"")

    def _parse(self):
        for instr in self.data["instructions"]:
            name = instr["name"]
            ops = instr.get("ops", []) 
            flags = instr.get("flags", [])
            desc = instr["desc"]
            self.instructions.append(InstructionDefinition(name, ops, flags, desc, self.next_encoding))
            self.next_encoding += 1

    def match(self, opcode_str: str, *args) -> InstructionDefinition:
        trial: list[InstructionDefinition] = []
        for i in self.instructions:
            if i.name == opcode_str:
                trial.append(i)
        
        if not trial:
            raise InvalidOpcodeException

        trial = [t for t in trial if len(t.ops) == len(args)]

        if not trial:
            raise InvalidOperandNumberException



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
        template_str = """| Name | Operands | Flags | Encoding | Description |
| ---- | -------- | ----- | -------- | ----------- |
{% for i in instructions %}| {{i.name}}   | {{", ".join(i.ops)}} | {{", ".join(i.flags)}} | {{i.encoding}} | {{i.desc}} |
{% endfor %}
"""
        template = Environment(loader=BaseLoader).from_string(template_str) 
        data = template.render({"instructions":self.instructions.instructions})

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
    instructions = ISADefinition(instruction_dict)

    formatter = Formatter(instructions)
    #if args.sv:
    #    formatter.render_sv("defs_pkg.sv")

    if args.cpp:
        formatter.render_cpp("defs_pkg.h")
    
    if args.table:
        formatter.render_table("defs.md")

if __name__ == "__main__":
    main()