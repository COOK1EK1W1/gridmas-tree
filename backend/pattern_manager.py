from types import ModuleType
from typing import Callable
import killableThread
import os
from colors import tcolors
from attribute import Store


def print_tabulated(item1: str, item2: str, item3: str, max_length: int):
    # Cap the length of each item
    item1 = item1[:max_length].ljust(max_length)
    item2 = item2[:max_length].ljust(max_length)
    item3 = str(item3)[:max_length].ljust(max_length)

    # Print the tabulated items
    print(f"{tcolors.OKGREEN}{item1}{item2}{item3}{tcolors.ENDC}")


def load_patterns(pattern_dir: str):
    print(f"{tcolors.OKBLUE}######## patterns ########{tcolors.ENDC}")
    pattern_files = [f for f in os.listdir(pattern_dir) if f.endswith(".py")]
    patterns: list[ModuleType] = []
    for file in pattern_files:
        print("loading pattern from " + "file" + "        ", end="\r")
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
    print(f"{tcolors.OKBLUE}######## patterns ########{tcolors.ENDC}\n")

    patterns.sort(key=lambda x: x.name.upper())
    return patterns


def run_pattern(fn: Callable[[], None]):
    try:
        print("running function")
        fn()
    except Exception as e:
        print(e)


class PatternManager:
    def __init__(self, pattern_dir: str):
        self.running_task: None | killableThread.Thread = None
        self.patterns = load_patterns(pattern_dir)
        self.run("on")

    def run(self, name: str) -> bool:
        pattern = self.get(name)
        if pattern is None:
            return False

        if self.running_task:
            self.running_task.terminate()
            self.running_task.join()
        Store.get_store().reset()
        self.running_task = killableThread.Thread(target=run_pattern, args=(pattern.run,))
        self.running_task.start()
        return True

    def get(self, name: str) -> ModuleType | None:
        patterns: list[ModuleType] = list(filter(lambda x: x.name == name, self.patterns))
        if len(patterns) == 0:
            return None
        return patterns[0]
