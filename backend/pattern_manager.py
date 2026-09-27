"""
    A collection of the pattern manager class and its helper functions
"""

from types import ModuleType
import os
import sys
from typing import Iterable
import traceback
import attribute
from pixel_driver import DriverRegistry
from util import tcolors
import math
import importlib
import time


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

        self.display_last_update = 0
        self.display_fps = 1/60

    def list_patterns(self) -> Iterable[str]:
        pattern_files = [f for f in os.listdir(self.pattern_dir) if f.endswith(".py")]
        return map(lambda x: x[:-3], pattern_files)

    def load_pattern(self, name: str) -> bool:
        """ load a pattern, true if success, false if failure """

        attribute.Store.get_store().reset()

        # the pattern now defined drivers, clear them before loading
        self.driver_registry.clear()

        module_string = self.pattern_dir.replace("/", ".") + f"{name}"
        print(f"Attempting to load pattern: {module_string}")

        try:
            existing = sys.modules.get(module_string)
            if existing is None:
                pattern_module = importlib.import_module(module_string)
            else:
                pattern_module = importlib.reload(existing)
        except Exception as e:
            traceback.print_exception(e)
            return False

        draw_function = pattern_module.update

        if draw_function is None:
            print("pattern does not have draw function")
            return False

        self.current_pattern_module = pattern_module

        return True

    def run_display_update(self):
        now = time.perf_counter()
        if self.current_pattern_module is not None and now > self.display_last_update + self.display_fps:
            self.current_pattern_module.update()
            self.display_last_update = now

    def unload_pattern(self):
        self.current_pattern = None
        self.generator = None

    def get_current_module(self) -> None | ModuleType:
        return self.current_pattern_module
