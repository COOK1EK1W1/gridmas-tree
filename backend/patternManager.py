import killableThread
import os
from colors import tcolors
from attribute import store
import time


def print_tabulated(item1, item2, item3, max_length):
    # Cap the length of each item
    item1 = item1[:max_length].ljust(max_length)
    item2 = item2[:max_length].ljust(max_length)
    item3 = str(item3)[:max_length].ljust(max_length)

    # Print the tabulated items
    print(f"{tcolors.OKGREEN}{item1}{item2}{item3}{tcolors.ENDC}")


def load_patterns(pattern_dir):
    print(f"{tcolors.OKBLUE}######## patterns ########{tcolors.ENDC}")
    pattern_files = [f for f in os.listdir(pattern_dir) if f.endswith(".py")]
    patterns = []
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

    return patterns


class PatternManager:
    def __init__(self, pattern_dir: str):
        self.running_task: None | killableThread.Thread = None
        self.patterns = load_patterns(pattern_dir)
        time.sleep(0.5)
        self.run("on")

    def run(self, name: str) -> bool:
        pattern = self.get(name)
        if pattern == None:
            return False

        if self.running_task:
            self.running_task.terminate()
            self.running_task.join()
        store.reset()
        self.running_task = killableThread.Thread(target=pattern.run)
        self.running_task.start()
        return True
    
    def get(self, name):
        patterns = list(filter(lambda x: x.name == name, self.patterns))
        if len(patterns) == 0:
            return None
        return patterns[0]

manager = PatternManager("patterns")
