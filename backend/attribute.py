class NumAttribute:
    def __init__(self, name: str, value: float, min: float|None = None, max: float|None = None):
        self.name = name
        self.value = value
        self.min = min
        self.max = max
        store.add(self)

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class ColorAttribute:
    def __init__(self, name: str, value: tuple[int, int, int]):
        self.name = name
        self.value = value
        store.add(self)

    def get(self):
        return self.value

    def set(self, value):
        pass



class Store:
    def __init__(self):
        self.store = []
    
    def reset(self):
        self.store = []

    def add(self, attr):
        self.store.append(attr)

    def __iter__(self):
        for x in self.store:
            yield x

    def get(self, name):
        return next(x for x in self.store if x.name == name)

    def set(self, name, value):
        a = next(x for x in self.store if x.name == name)
        print(a)
        a.set(value)

store = Store()
