"""
    A collection of the pattern manager class and its helper functions
"""

import os
import sys
from types import ModuleType
from typing import Iterable
import traceback
import attribute
from pixel_driver import DriverRegistry
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
    def __init__(self, pattern_dir: str, driver_registry: DriverRegistry):
        self.pattern_dir = pattern_dir

        self.current_pattern_module: ModuleType | None = None
    
        self.driver_registry = driver_registry

    def list_patterns(self) -> Iterable[str]:
        pattern_files = [f for f in os.listdir(self.pattern_dir) if f.endswith(".py")]
        return map(lambda x: x[:-3], pattern_files)

    def load_pattern(self, name: str) -> bool:
        """ load a pattern, true if success, false if failure """

        attribute.Store.get_store().reset()

        # A display module registers its fixtures and drivers as a side effect
        # of being imported, so the outgoing display's drivers have to be shut
        # down before the incoming ones dial the device - a device only serves
        # one controller at a time.
        self.driver_registry.clear()

        module_string = self.pattern_dir.replace("/", ".") + f"{name}"
        print(f"Attempting to load pattern: {module_string}")

        try:
            existing = sys.modules.get(module_string)
            if existing is None:
                pattern_module = importlib.import_module(module_string)
            else:
                # Exactly one execution per load, either way. `__import__`
                # followed by `reload` ran the module body twice, which for a
                # display module meant two of every driver - both then fighting
                # over the device's single controller slot.
                pattern_module = importlib.reload(existing)
        except Exception as e:
            traceback.print_exception(e)
            return False

        draw_function = None

        if draw_function is None and False:
            print("pattern does not have draw function")
            return False

        self.current_pattern_module = pattern_module
        #self.driver_registry.update_draw(draw_function)

        return True

    def unload_pattern(self):
        self.current_pattern = None
        self.generator = None

    def get_current_module(self) -> None | ModuleType:
        return self.current_pattern_module
