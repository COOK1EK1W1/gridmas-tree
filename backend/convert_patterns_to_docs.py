""" Automatically create documentation for sample code

Run download-patterns.py first.
Then run this. 

Will take all sample code, match it with a markdown file and dump the contents inside.
"""

__version__ = "1.0.0"
__author__ = "Owen Plimer"

from os import listdir

PATTERNS_DIR = r"backend\patterns"
DOCS_DIR = r"docs\samples"

for file in listdir(PATTERNS_DIR):
    if file.endswith(".py"):
        
        # Get the contents of the pattern file
        with open(fr"{PATTERNS_DIR}\{file}", "r") as in_file:
            pattern_code = in_file.read()
            
        # Now, open the md file for the pattern if it exists, otherwise make a new one
        with open(fr"{DOCS_DIR}\{file.replace(".py", ".md")}", "w") as out_file:
            # Finally write to the file
            # First the header
            out_file.write(f"# {file.strip(".py")}\n")
            
            # Now the start of the code segment
            out_file.write('```py linenums="1"\n')
            
            # Now the pattern code
            out_file.write(pattern_code)
            
            # Now the end of the code segment
            out_file.write("\n```")