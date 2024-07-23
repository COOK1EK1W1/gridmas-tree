from abc import ABC, abstractmethod
from colors import Color
from typing import TypeVar, Generic


def clamp(val: float | int, minv: float | int, maxv: float | int) -> float | int:
    return min(max(val, minv), maxv)


T = TypeVar("T")


class Attribute(Generic[T], ABC):
    def __init__(self, name: str, value: T):
        self.name = name
        self.value: T = value

    def get(self) -> T:
        return self.value

    def set(self, value: T):
        self.value = value

    @abstractmethod
    def pattern_string(self) -> str:
        ...


class RangeAttr(Attribute[float]):
    def __init__(self, name: str,
                 value: float,
                 min: float,
                 max: float,
                 step: float):
        self.min = min
        self.max = max
        super().__init__(name, float(clamp(value, self.min, self.max)))
        self.step = step
        Store.get_store().add(self)

    def pattern_string(self):
        return 'RangeAttr.html'


class ColorAttr(Attribute[Color]):
    def __init__(self, name: str, value: Color):
        super().__init__(name, value)
        Store.get_store().add(self)

    def pattern_string(self):
        return "ColorAttr.html"


class Store:
    instance: "None | Store" = None

    def __init__(self):
        self.store: list[ColorAttr | RangeAttr] = []

    def reset(self):
        self.store = []

    def add(self, attr: ColorAttr | RangeAttr):
        self.store.append(attr)

    def __iter__(self):
        for x in self.store:
            yield x

    def get(self, name: str):
        return next(x for x in self.store if x.name == name)

    def get_all(self):
        return self.store

    @classmethod
    def get_store(cls):
        if cls.instance is None:
            newstore = Store()
            cls.instance = newstore
        return cls.instance
