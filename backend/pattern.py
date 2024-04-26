import os
from colors import tcolors


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

            name = pattern_module.name
            display_name = pattern_module.display_name
            func = pattern_module.run
            print_tabulated(name, display_name, func, 20)
            patterns.append(pattern_module)

        except Exception as e:
            print(f"{tcolors.FAIL}skipping {file} | wrong configuration | {e} {tcolors.ENDC}")
    print(f"{tcolors.OKBLUE}######## patterns ########{tcolors.ENDC}\n")

    return patterns
