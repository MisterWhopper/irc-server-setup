from __future__ import annotations
from ast import literal_eval
from collections.abc import Container
from dataclasses import dataclass, field
from pathlib import Path
from secrets import token_hex
from string import Template
from typing import Any, Protocol
import argparse
import json
import re
import sys

VARIABLE_PATTERN = re.compile(r'\$\{[\w_.]+\}|\$[\w_]+')

class IValueMapper(Protocol):
    """
    For when you need 'true' to become 'True' and such.
    """
    def map(self, value: Any) -> str: ...

@dataclass
class ValueGenerator:
    _map: dict = field(default_factory=dict)

    def register(self, input_arg):
        def dec_factory(func):
            if func.__name__ not in self._map:
               self._map[func.__name__] = {"func": func, "arg": input_arg.replace(".", "_dot_")} 
            return func
        return dec_factory

    def add_generated_values(self, var_full_name: str, values: dict[str, str]) -> dict[str, str]:
        # Don't generate a value twice
        if var_full_name not in values:
            key_name = var_full_name.split("_gen_dot_")[-1]
            val_input = values.get(self._map.get(key_name, {}).get("arg"))
            functor = self._map.get(key_name, {}).get("func", lambda i: print(f"Couldn't find mapping for '{i}'"))
            if self._map.get(key_name) is not None and functor is not None:
                values[var_full_name] = functor(val_input)
        return values 

ircd_generator = ValueGenerator()

def sanitize_dict(values: dict[str, Any], value_mapper: IValueMapper) -> dict[str, str]:
    results = {}
    for k, v in values.items():
        if isinstance(v, dict):
            their_dict = sanitize_dict({f"{k}_dot_{n}": i for n, i in v.items()}, value_mapper)
            results.update(their_dict)
        results[k] = value_mapper.map(v)
    return results

def hydrate_file(file: Path, values: dict[str, str]) -> str:
    if not file.exists() or file.stat().st_size == 0:
        raise FileNotFoundError()
    raw_text = file.read_text()
    placeholder_values = re.findall(VARIABLE_PATTERN, raw_text)
    if not placeholder_values:
        return raw_text
    # Since Python's string.Template class doesn't allow periods for some unknown reason, change the names
    placeholders_fixed = [s.replace(".", "_dot_") for s in placeholder_values]
    corrected_text = raw_text
    for current, new in zip(placeholder_values, placeholders_fixed):
        corrected_text = corrected_text.replace(current, new)
        if "_dot__gen_" in new:
            var_full_name = new.replace("$","").replace("{","").replace("}","")
            values = ircd_generator.add_generated_values(var_full_name, values)
    templ = Template(corrected_text)
    semi_final_text = templ.safe_substitute(values)
    # Swap the corrected values back for their original selves (it'll bother me otherwise)
    for new, current in zip(placeholder_values, placeholders_fixed):
        semi_final_text = semi_final_text.replace(current, new)
    return semi_final_text
            
@dataclass
class CliArgs:
    templ_file: Path
    data_file: Path
    output_file: Path | Any

    @staticmethod
    def parse() -> CliArgs:
        parser = argparse.ArgumentParser(prog="templatinator.py", description="Simple JSON template engine.")
        parser.add_argument("-i", type=Path, dest="templ_file", help="Input template file", required=True)
        parser.add_argument("-d", type=Path, dest="data_file", help="JSON file with template values", required=True)
        parser.add_argument("-o", type=Path, dest="output_file", help="Target output file (default STDOUT)", default=sys.stdout)
        args = vars(parser.parse_args())
        return CliArgs(**args)

@ircd_generator.register("ircd.accepted_countries")
def accepted_countries(entries_raw: str) -> str:
    # First convert from string literal to list of strings 
    entries = literal_eval(entries_raw)
    # Have to this the old-fashioned way, as f-strings freak out over nested brackets
    if isinstance(entries, Container):
        return "country { %s; };" % '; '.join(e for e in entries)
    elif isinstance(entries, str):
        return "country { %s; };" % entries
    else:
        raise ValueError(f"Expected list of country code strings, or single country code string. Got '{entries}' instead (type={type(entries)})")

@ircd_generator.register("ircd.max_clients")
def opers_max_clients(max_clients: str) -> str:
    as_int = int(max_clients)
    return str(round(as_int * 1.5))

@ircd_generator.register("")
def admin_password(_) -> str:
    return token_hex(16)

@ircd_generator.register("")
def clk_keys(_) -> str:
    # Need 3 quoted, long-ass strings
    keys = [f"\"{token_hex(48)}\";" for _ in range(3)]
    return ('\n' + (' ' * 12)).join(keys)

@ircd_generator.register("ircd.log_maxsize")
def json_log_maxsize(maxsize_str: str) -> str:
    numbers = re.findall(r'\d+', maxsize_str)[0]
    suffix = maxsize_str.split(numbers)[-1]
    as_int = int(numbers)
    return f"{round(as_int * 1.5)}{suffix}"

class DefaultMapper:
    def map(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return str(value)

def main():
    args = CliArgs.parse()
    data_values = sanitize_dict(json.loads(args.data_file.read_text()), DefaultMapper())
    final_text = hydrate_file(args.templ_file, data_values)
    if isinstance(args.output_file, Path):
        args.output_file.write_text(final_text)
    else:
        sys.stdout.write(final_text)

if __name__ == "__main__":
    main()
