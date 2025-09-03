from types import GeneratorType, ModuleType
import os
from typing import Generator
import attribute
from util import tcolors
import math
import importlib


def print_tabulated(item1: str, item2: str, item3: str, max_length: int):
    # Cap the length of each item
    item1 = item1[:max_length].ljust(max_length)
    item2 = item2[:max_length].ljust(max_length)
    item3 = str(item3)[:max_length].ljust(max_length)

    # Print the tabulated items
    print(f"{tcolors.OKGREEN}{item1}{item2}{item3}{tcolors.ENDC}")


def print_message_centered(msg: str, min_len: int, padding: str = " ") -> str:
    if len(msg) > min_len:
        return msg
    msg = " " + msg + " "
    if len(msg) > min_len:
        return msg
    padding_needed = min_len - len(msg)
    l_padding = math.floor(padding_needed / 2)
    r_padding = math.ceil(padding_needed / 2)
    return padding * l_padding + msg + padding * r_padding




class PatternManager:
    def __init__(self, pattern_dir: str):
        self.load_patterns(pattern_dir)

        self.currentPattern = self.patterns["on"]

        self.generator = None

    def load_patterns(self, pattern_dir: str):

        print(f"{tcolors.OKBLUE}{print_message_centered('Loading Patterns', 60, '#')}{tcolors.ENDC}")

        pattern_files = [f for f in os.listdir(pattern_dir) if f.endswith(".py")]
        patterns: dict[str, ModuleType] = {}
        for file in pattern_files:
            print("loading pattern from " + file + "        ", end="\r")
            try:
                module_name = os.path.splitext(file)[0]
                module = __import__("patterns." + module_name)
                pattern_module = getattr(module, module_name)

                pattern_module.draw
                name = module_name
                print_tabulated(name, "", "", 20)
                patterns[name] = pattern_module

            except Exception as e:
                print(f"{tcolors.FAIL}skipping {file} | wrong configuration | {e} {tcolors.ENDC}")

        print(f"{tcolors.OKBLUE}{print_message_centered('Loading Patterns', 60, '#')}{tcolors.ENDC}")

        attribute.Store.get_store().reset()
        self.patterns = patterns


    def draw_current(self):
        if self.currentPattern != None:
            try:
                if self.generator:
                    next(self.generator)
                else:
                    res: Generator[None, None, None] | None = self.currentPattern.draw()
                    if isinstance(res, GeneratorType):
                        self.generator = res
            except Exception as e:
                self.generator = None
                self.currentPattern = None
                print("There was an error", e)


    def load_pattern(self, name: str):
        """TODO fix so people cant just inject whatever name they want from client side :skull:"""
        attribute.Store.get_store().reset()
        module = __import__("patterns." + name)
        pattern_module = getattr(module, name)
        importlib.reload(pattern_module)
        self.currentPattern = self.patterns[name]
        self.generator = None
        print(attribute.Store.get_store().store)

    def unload_pattern(self):
        self.currentPattern = None
        self.generator = None

    def get(self, name: str):
        return self.patterns[name]
