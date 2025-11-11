import json
import requests

with open("patterns/patterns.json") as file:
    data = json.loads(file.read())

    # Extract all pattern IDs
    pattern_ids = [pattern['id'] for pattern in data]
    
    # Create comma-separated string of IDs
    ids_param = ','.join(pattern_ids)
    
    # Make single request to get all patterns
    res = requests.get(f"https://gridmas-tree.vercel.app/api/get-pattern?ids={ids_param}")
    patterns_data = res.json()
    print(patterns_data)
    
    # Handle both single pattern (object) and multiple patterns (array) responses
    if isinstance(patterns_data, list):
        # Multiple patterns returned as array
        for patternData in patterns_data:
            print(f"Downloading: {patternData['title']}")
            with open(f"patterns/{patternData['title']}.py", "w+") as f:
                f.write(patternData["data"])
    else:
        # Single pattern returned as object
        print(f"Downloading: {patterns_data['title']}")
        with open(f"patterns/{patterns_data['title']}.py", "w+") as f:
            f.write(patterns_data["data"])




