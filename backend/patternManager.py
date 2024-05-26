from pattern import load_patterns
import killableThread
from attribute import store

class PatternManager:
    def __init__(self, pattern_dir: str):
        self.running_task: None | killableThread.Thread = None
        self.patterns = load_patterns(pattern_dir)

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
