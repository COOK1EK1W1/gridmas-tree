from abc import ABC, abstractmethod
from colors import Color
from typing import TypeVar, Generic


def clamp(val, minv, maxv):
    return min(max(val, minv), maxv)


T = TypeVar("T")


class Attribute(Generic[T], ABC):
    def __init__(self, name: str, value: T):
        self.name = name
        self.value = value
        store.add(self)

    def get(self) -> T:
        return self.value

    def set(self, value):
        self.value = value

    @abstractmethod
    def pattern_string(self) -> str:
        ...


class RangeAttr(Attribute):
    def __init__(self, name: str,
                 value: float,
                 min: float,
                 max: float,
                 step: float):
        super().__init__(name, value)
        self.min = min
        self.max = max
        self.step = step
        clamp(self.value, self.min, self.max)

    def pattern_string(self):
        return 'RangeAttr.html'


class ColorAttr(Attribute):
    def __init__(self, name: str, value: Color):
        super().__init__(name, value)

    def pattern_string(self):
        return "ColorAttr.html"


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

    def get_all(self):
        return self.store


store = Store()
