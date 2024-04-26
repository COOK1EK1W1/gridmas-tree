from abc import ABC, abstractmethod
from typing import TypeVar, Generic

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


class NumAttribute(Attribute):
    def __init__(self, name: str,
                 value: float,
                 min: float | None = None,
                 max: float | None = None):
        super().__init__(name, value)
        self.min = min
        self.max = max

    def pattern_string(self):
        return 'numAttribute.html'


class ColorAttribute(Attribute):
    def __init__(self, name: str, value: tuple[int, int, int]):
        self.name = name
        self.value = value
        store.add(self)


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
