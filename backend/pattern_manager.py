"""
    A collection of the pattern manager class and its helper functions
"""

from types import GeneratorType, ModuleType
import os
from typing import Generator
import attribute
from util import tcolors
import math
import importlib


def print_tabulated(item1: str, item2: str, item3: str, max_length: int):
    """print_tabulated Print a table

    Print a table of three columns wide

    Args:
        item1 (str): The first column text
        item2 (str): The second column text
        item3 (str): The third column text
        max_length (int): The maximum length of text allow in a column
    """
    # Cap the length of each item
    item1 = item1[:max_length].ljust(max_length)
    item2 = item2[:max_length].ljust(max_length)
    item3 = str(item3)[:max_length].ljust(max_length)

    # Print the tabulated items
    print(f"{tcolors.OKGREEN}{item1}{item2}{item3}{tcolors.ENDC}")


def print_message_centered(msg: str, min_len: int, padding: str = " ") -> str:
    """print_message_centered Print a message that is centered in the terminal

    Creates a message string that contains the message and the required padding to make it appear in the center

    Args:
        msg (str): The message to display
        min_len (int): The minimum length of the message for it to be centered
        padding (str, optional): The character to use for padding the message. Defaults to " ".

    Returns:
        str: The padded message
    """
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
    """ Manages patterns for the tree

    The pattern manager is in charge of loading, parsing, storing and recalling pattern files
    
    Warning:
        This module is intended for internal use only. You do not need to use any of this in your pattern code
    """
    
    def __init__(self, pattern_dir: str):
        """__init__ Initialise the pattern manager

        Create a new instance of the pattern manager and load the `on` pattern

        Args:
            pattern_dir (str): The directory to search for pattern files. The search is carried out automatically
        """
        self.load_patterns(pattern_dir)

        self.currentPattern = self.patterns["on"]

        self.generator = None

    def load_patterns(self, pattern_dir: str):
        """load_patterns Loads the patterns from the pattern_dir

        Searches for .py files inside the python file, and then tries to import them

        Args:
            pattern_dir (str): The directory to search in
        """

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
        """draw_current Draw the current pattern

        Takes the currently loaded pattern and runs it, if no pattern is loaded then nothing will happen
        """
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
        """load_pattern Loads a pattern

        Load the pattern with a given name from the patterns directory

        Args:
            name (str): _description_
            
        Note:
            TODO fix so people cant just inject whatever name they want from client side :skull:
        """
        attribute.Store.get_store().reset()
        module = __import__("patterns." + name)
        pattern_module = getattr(module, name)
        importlib.reload(pattern_module)
        self.currentPattern = self.patterns[name]
        self.generator = None
        print(attribute.Store.get_store().store)

    def unload_pattern(self):
        """unload_pattern Resets the manager state

        Reset the current pattern and generator variables to effectively restart the manager
        """
        
        self.currentPattern = None
        self.generator = None

    def get(self, name: str):
        """get Gets a pattern

        Feteches the pattern with a given name from the internal pattern list, then returns it

        Args:
            name (str): The name of the pattern you want to fetch

        Returns:
            code (str): Returns the python code of the pattern
        """
        
        return self.patterns[name]
