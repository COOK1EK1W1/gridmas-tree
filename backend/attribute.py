"""Attributes allow you to change parameters of your pattern while the pattern is running from
   the web interface, this helps create more dynamic and customizable patterns

    Attributes should be initiallised before/outside of the draw() function
"""
from abc import ABC, abstractmethod
from colors import Color
from typing import TypeVar, Generic, Union, Optional


def clamp(val: Union[float, int], minv: Union[float, int], maxv: Union[float, int]) -> Union[float, int]:
    return min(max(val, minv), maxv)


T = TypeVar("T")


class Attribute(Generic[T], ABC):
    """Only initialise attributes once in the run function

    This class should not be instantiated, it is a base class
    """

    def __init__(self, name: str, value: T):
        self.name = name
        self.value: T = value

    def get(self) -> T:
        """Get the current value of the attribute

        Returns:
            T: The value of the attribute
        """
        return self.value

    def set(self, value: T):
        """Set the value of the range.

           The use of this is discouraged in a pattern, it is primarily an internal function

        Args:
            value (T): The value to set the attribute to
        """
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
        """Used when you want to accept a value from a pre defined range

        Args:
            name (str): The name displayed on the interface
            value (float): The default starting value
            min (float): The minimum value accepted
            max (float): The maximum value accepted
            step (float): The resolution for the range

        Example:
            ```
            speed = RangeAttr("speed", 0.2, -1, 1, 0.2)
            def draw()
                print(speed.get())
            ```
        """
        self.min = min
        self.max = max
        super().__init__(name, float(clamp(value, self.min, self.max)))
        self.step = step
        Store.get_store().add(self)

    def pattern_string(self):
        return 'RangeAttr.html'


class ColorAttr(Attribute[Color]):
    def __init__(self, name: str, value: Color):
        """Used when you want to accept a color as an input

        Args:
            name (str): The name displayed on the interface
            value (Color): The initial color

        Example:
            ```
            color1 = ColorAttr("color1", Color.red())
            def draw()
                fill(color1.get())
            ```
        """
        super().__init__(name, value)
        Store.get_store().add(self)

    def pattern_string(self):
        return "ColorAttr.html"


class Store:
    instance: "Optional[Store]" = None

    def __init__(self):
        self.store: list[Union[ColorAttr, RangeAttr]] = []

    def reset(self):
        self.store = []

    def add(self, attr: Union[ColorAttr, RangeAttr]):
        self.store.append(attr)

    def __iter__(self):
        for x in self.store:
            yield x

    def get(self, name: str):
        return list(x for x in self.store if x.name == name)[0]

    def get_all(self):
        return self.store

    @classmethod
    def get_store(cls):
        if cls.instance is None:
            newstore = Store()
            cls.instance = newstore
        return cls.instance
