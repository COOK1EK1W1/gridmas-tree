from types import ModuleType
import random
import time
import threading
from typing import Callable
from util import STOPFLAG
import os
from colors import tcolors
from attribute import Store
from tree import tree
import math


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


def load_patterns(pattern_dir: str):

    print(f"\n{tcolors.OKBLUE}{print_message_centered('loading patterns', 60, '#')}{tcolors.ENDC}")

    pattern_files = [f for f in os.listdir(pattern_dir) if f.endswith(".py")]
    patterns: list[ModuleType] = []
    for file in pattern_files:
        print("loading pattern from " + file + "        ", end="\r")
        try:
            module_name = os.path.splitext(file)[0]
            module = __import__("patterns." + module_name)
            pattern_module = getattr(module, module_name)

            name = module_name
            display_name = pattern_module.name
            func = pattern_module.run
            print_tabulated(name, display_name, func, 20)
            patterns.append(pattern_module)

        except Exception as e:
            print(f"{tcolors.FAIL}skipping {file} | wrong configuration | {e} {tcolors.ENDC}")

    print(f"{tcolors.OKBLUE}{print_message_centered('loading patterns', 60, '#')}{tcolors.ENDC}")

    patterns.sort(key=lambda x: x.name.upper())
    return patterns


def run_pattern(name: str, fn: Callable[[], None]):
    try:
        fn()
    except STOPFLAG:
        tree.stop_flag = False
    except Exception as e:
        print(tcolors.FAIL + "####### PATTERN ERROR ######")
        print(f"pattern name: {name}")
        print(e)
        print("############################" + tcolors.ENDC)


class PatternManager:
    def __init__(self, pattern_dir: str):
        self.lock = threading.Lock()
        self.running_task: None | threading.Thread = None
        self.patterns = load_patterns(pattern_dir)
        self.pattern_queue: list[str] = ["on"]

        self.idle_stop_flag = False
        self.running_name = ""

        a = threading.Thread(target=self.start)
        a.start()

    def start(self):
        while True:
            time.sleep(0.01)
            if len(self.pattern_queue) > 0:
                pattern = self.pattern_queue.pop(0)
                self.run(pattern)

    def queue_pattern(self, name: str):
        self.pattern_queue.append(name)
        return True

    def random_patterns(self):
        running = None
        while not self.idle_stop_flag:
            if running:
                if running.is_alive():
                    tree.stop_flag = True
                    running.join()
            Store.get_store().reset()
            tree.set_fps(45)
            i = random.randrange(0, len(self.patterns))
            pattern = self.patterns[i]
            print(pattern.name)
            tree.pixel_driver.clear_queue()
            running = threading.Thread(target=run_pattern, args=(pattern.name, pattern.run,))
            running.start()
            time.sleep(30)
        self.idle_stop_flag = False

    def run(self, name: str) -> bool:
        with self.lock:
            if name == "idle":
                if self.running_task and self.running_task.is_alive():
                    tree.stop_flag = True
                    self.running_task.join()
                Store.get_store().reset()
                tree.set_fps(45)
                tree.pixel_driver.clear_queue()
                self.running_task = threading.Thread(target=self.random_patterns)
                self.running_task.start()
                self.running_name = name
                return True

            pattern = self.get(name)
            if pattern is None:
                return False

            if self.running_task and self.running_task.is_alive():
                if self.running_name == "idle":
                    self.idle_stop_flag = True
                tree.stop_flag = True
                self.running_task.join()
            Store.get_store().reset()
            tree.set_fps(45)
            tree.pixel_driver.clear_queue()
            self.running_task = threading.Thread(target=run_pattern, args=(name, pattern.run,))
            self.running_task.start()
            self.running_name = name
            return True

    def get(self, name: str) -> ModuleType | None:
        patterns: list[ModuleType] = list(filter(lambda x: x.name == name, self.patterns))
        if len(patterns) == 0:
            return None
        return patterns[0]
