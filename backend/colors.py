""" colors is a module which contains class definitions for Color and Pixel as well as
    helper functions for converting colors between formats

   I appologise to all british programmers who spell color as colour, but within the
   programming world we spell it color. This will be the cause of 90% of your bugs
   if you're not use to programming with the color spelling
"""

import random
import math
import time
import colorsys
from typing import Callable, Union

from util import linear




class tcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def clamp(val: Union[float, int], minv: Union[float, int], maxv: Union[float, int]):
    return min(max(val, minv), maxv)


class Color:
    """A class representing a color

       Attributes:
       r: int: Red
       g: int: Green
       b: int: Blue
    """

    def __init__(self, r: int, g: int, b: int):
        self.changed = False
        self._r: int = r & 0xff
        self._g: int = g & 0xff
        self._b: int = b & 0xff

        self._L_previous = (0, 0, 0)
        self._L_target = (0, 0, 0)

        self._L_step = 0
        self._L_total = 1

        self._L_fn = linear

    @property
    def r(self):
        return self._r

    @property
    def g(self):
        return self._g

    @property
    def b(self):
        return self._b

    def set_rgb(self, r: int, g: int, b: int):
        """Set the red, green and blue values of the color.
           All params are bounded between 0 and 255

        Args:
            r (int): Red value: 0 - 255
            g (int): Green value: 0 - 255
            b (int): Blue value: 0 - 255
        """
        self._r = r & 0xff
        self._g = g & 0xff
        self._b = b & 0xff

        self.lerp_reset()
        self.changed = True

    def set_color(self, color: 'Color'):
        """Set the color to another named color.

        Args:
            color (Color): Named color
        """
        self.set_rgb(*color.to_tuple())
        self.changed = True

    def fade(self, n: float = 1.1):
        """Fade the color slightly

        Args:
            n (float, optional): The greater the value of n, the faster the fade will progress. Values less than 0 cause the color to get brighter to a max color of white. Defaults to 1.1.
        """
        self._r = int(clamp(self.r / n, 0, 255))
        self._g = int(clamp(self.g / n, 0, 255))
        self._b = int(clamp(self.b / n, 0, 255))

        self.lerp_reset()
        self.changed = True

    def to_hex(self) -> str:
        """Returns the hex value of an RGB color

        Returns:
            str: The hex value of the color
        """
        return tuple2hex((self.r, self.g, self.b))

    def to_tuple(self) -> tuple[int, int, int]:
        """Returns the tuple of the R, G and B values between 0 and 255

        Returns:
            tuple[int, int, int]: [Red, Green, Blue]
        """
        return (self.r, self.g, self.b)

    def to_int(self) -> int:
        """Return the color as an integer

        Returns:
            int: Color represented as an integer
        """
        return (self.r << 8) | (self.g << 16) | self.b

    def lerp_reset(self):
        self._L_previous = (self.r, self.g, self.b)
        self._L_step = 0

    def lerp(self, target: tuple[int, int, int], time: int, override: bool = False, fn: Callable[[float], float] = linear):
        """Linearly interpolate the color from its current color to the target color

        Args:
            target (tuple[int, int, int]): The target color
            time (int): The time taken for the lerp to complete
            override (bool, optional): If set to true, the lerp will only progress when you call lerp again. Defaults to False.
            fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
        """
        self.set_lerp(target, time, override, fn)
        self.cont_lerp()

    def set_lerp(self, target: tuple[int, int, int], time: int, override: bool = False, fn: Callable[[float], float] = linear):
        """This resets the lerp and starts interpolation to the target from the current value.

        Args:
            target (tuple[int, int, int]): Target color
            time (int): Time taken to complete the lerp
            override (bool, optional): If true, the target can be changed while the lerp is in progress. Defaults to False.
            fn (Callable[[float], float], optional): Timing function from the Util module. Defaults to linear.
        """
        if (target != self._L_target or self._L_total != time) or override:
            self.lerp_reset()
            self._L_target = target
            self._L_total = time
            self._L_fn = fn

    def cont_lerp(self):
        """Advanced the lerp one step.
        """
        if self._L_step == self._L_total:
            return
        self._L_step = min(self._L_step + 1, self._L_total)
        percent = clamp(self._L_step / self._L_total, 0, 1)
        d = self._L_fn(percent)

        self._r = int(self._L_previous[0] * (1 - d) + self._L_target[0] * d)
        self._g = int(self._L_previous[1] * (1 - d) + self._L_target[1] * d)
        self._b = int(self._L_previous[2] * (1 - d) + self._L_target[2] * d)
        self.changed = True

    @staticmethod
    def from_hex(s: str) -> 'Color':
        """Get a color from a string hex code

        Args:
            s (str): The hex color

        Returns:
            Color: (r,g,b) repsentation of the color
        """
        return Color(int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))

    @staticmethod
    def from_hsl(hue: float, sat: float, lig: float) -> 'Color':
        """Get a color from hsl format

        Args:
            hue (float): The hue of the target color
            sat (float): The saturation of the target color
            lig (float): The lightness of the target color

        Returns:
            Color: (r,g,b) repsentation of the color
        """
        r, g, b = colorsys.hsv_to_rgb(hue, sat, lig)
        return Color(int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def random(saturation: float = 1, lightness: float = 0.6) -> 'Color':
        """Generate a random color.
           The random value is for the Hue. The saturation and lightness can be specified

        Args:
            saturation (float, optional): The target saturation. Defaults to 1.
            lightness (float, optional): The target lightness. Defaults to 0.6.

        Returns:
            Color: The color that is generated
        """
        return Color.from_hsl(random.random(), saturation, lightness)

    @staticmethod
    def different_from(color: 'Color') -> 'Color':
        """Generate a random color which is different from the color passed into it, maintaining the same hue and saturation

        Args:
            color (Color): The color which is currently in use

        Returns:
            Color: A color which is different from the one passed into the function
        """
        h, s, v = colorsys.rgb_to_hsv(*color.to_tuple())
        newh = ((h * 360 + random.randint(0, 180) + 40) % 360) / 360
        nr, ng, nb = colorsys.hsv_to_rgb(newh, s, v)
        return Color(int(nr), int(ng), int(nb))

    @staticmethod
    def black():
        return Color(0, 0, 0)

    @staticmethod
    def red():
        return Color(255, 0, 0)

    @staticmethod
    def orange():
        return Color(252, 81, 8)

    @staticmethod
    def amber():
        return Color(251, 136, 10)

    @staticmethod
    def yellow():
        return Color(234, 163, 8)

    @staticmethod
    def lime():
        return Color(107, 202, 3)

    @staticmethod
    def green():
        return Color(0, 255, 0)

    @staticmethod
    def emerald():
        return Color(23, 178, 106)

    @staticmethod
    def teal():
        return Color(23, 175, 150)

    @staticmethod
    def cyan():
        return Color(21, 170, 210)

    @staticmethod
    def sky():
        return Color(20, 146, 241)

    @staticmethod
    def blue():
        return Color(0, 0, 255)

    @staticmethod
    def indigo():
        return Color(78, 64, 255)

    @staticmethod
    def violet():
        return Color(122, 47, 255)

    @staticmethod
    def purple():
        return Color(155, 30, 255)

    @staticmethod
    def fuchsia():
        return Color(215, 0, 250)

    @staticmethod
    def pink():
        return Color(240, 15, 137)

    @staticmethod
    def rose():
        return Color(251, 0, 69)

    @staticmethod
    def white():
        return Color(255, 255, 255)


class Pixel(Color):
    """The pixel class extends the Color class by adding 3D coordinates to a color.
       All the same methods and attributes exist on a pixel so they act the same way

       Coordintates are in the GIFT format so range between -1 and 1 on X and Y axis,
       and 0 and tree.height on the Z axis

       Attributes:
       x: float: The x axis position
       y: float: The y axis position
       z: float: The z axis position
       a: float: The polar angle in radians from the x axis going clockwise when looking downward on the tree
       d: float: The polar distance from the Z axis (trunk)
    """

    def __init__(self, coord: tuple[float, float, float], color: Color = Color.black()):
        super().__init__(*color.to_tuple())
        self.x = coord[0]
        self.y = coord[1]
        self.z = coord[2]

        self.a = math.atan2(self.y, self.x)
        self.d = math.sqrt(self.y ** 2 + self.x ** 2)


def int2tuple(c: int) -> tuple[int, int, int]:
    """conver the 24bit encoded int to tuple of R, G, and B.

       int bitmap encoded as GGGGGGGGRRRRRRRRBBBBBBBB

    Args:
        c (int): Color represented as an int

    Returns:
        tuple[int, int, int]: R,G,B bitmap of the input color
    """
    return ((c >> 8) & 0xff, (c >> 16) & 0xff, c & 0xff)


def tuple2hex(t: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to hex string

    Args:
        t (tuple[int, int, int]): RGB color

    Returns:
        str: Hex value of the color
    """
    return '#%02x%02x%02x' % t


def hex2tuple(h: str) -> tuple[int, int, int]:
    """Convert a hex string to an RGB tuple

    Args:
        h (str): Hex string of a color

    Returns:
        tuple[int, int, int]: RGB tuple of the color
    """
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


if __name__ == "__main__":
    tests = [(0, 0, 0), (255, 255, 255), (0, 100, 0), (100, 0, 0), (0, 0, 100)]
    for test in tests:
        ans = hex2tuple(tuple2hex(test))
        if ans != test:
            raise Exception("error in")

    tests2 = list(map(lambda x: tuple2hex(x), tests))
    for test in tests2:
        ans = tuple2hex(hex2tuple(test))
        if ans != test:
            raise Exception("error in")

    for test in tests:
        ans = colorsys.hsv_to_rgb(*colorsys.rgb_to_hsv(*test))
        if ans != test:
            print(test, ans)
            raise Exception("error in")

if __name__ == "__main__" and False:
    a = time.perf_counter()
    for i in range(10_000_000):
        newColor = Color(1, 2, 3)
        newColor.set_rgb(3, 2, 1)
        newColor.fade()
    print(time.perf_counter() - a)

if __name__ == "__main__":
    red = Color.red()

    red.lerp((0, 0, 0), 5)
    if red.to_tuple() != (204, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp((0, 0, 0), 5)
    if red.to_tuple() != (153, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp((0, 0, 0), 5)
    if red.to_tuple() != (102, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp((0, 0, 0), 5)
    if red.to_tuple() != (50, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp((0, 0, 0), 5)
    if red.to_tuple() != (0, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp((0, 0, 0), 5)
    if red.to_tuple() != (0, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")
