""" Colors is a module which contains class definitions for Color and Pixel as well as
    helper functions for converting colors between formats

   I appologise to all british programmers who spell color as colour, but within the
   programming world we spell it color. This will be the cause of 90% of your bugs
   if you're not used to programming with the color spelling
"""

import random
import math
import colorsys
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tree import Tree
from typing import Callable

from util import linear, clamp



class Color:
    """A class representing a color"""

    def __init__(self, r: int, g: int, b: int):
        self._changed = False
        self._r: int = r & 0xff
        self._g: int = g & 0xff
        self._b: int = b & 0xff

        self._L_previous = [0, 0, 0]
        self._L_target = [0, 0, 0]

        self._L_step = 0
        self._L_total = 0

        self._L_fn = linear

    @property
    def r(self):
        """Red component 0-255"""
        return self._r

    @property
    def g(self):
        """Green component 0-255"""
        return self._g

    @property
    def b(self):
        """Blue component 0-255

            example:
                ```py
                myColor = Color(255, 100, 120)
                print(myColor.r) # 255
                print(myColor.g) # 100
                print(myColor.b) # 120
                ```
        """
        return self._b

    """
    ### Static methods
    """

    @staticmethod
    def rgb(r: int, g: int, b: int) -> 'Color':
        """An alias for the constructor, values between 0 and 255

        example:
            ```py
            red = Color.rgb(255, 0, 0)
            blue = Color.rgb(0, 255, 0)
            green = Color.rgb(0, 0, 255)
            ```
        """
        return Color(r, g, b)

    @staticmethod
    def hsl(hue: float, sat: float, lig: float) -> 'Color':
        """Get a color from hsl format, values between 0 and 1.0"""
        r, g, b = colorsys.hsv_to_rgb(hue, sat, lig)
        return Color(int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def hex(s: str) -> 'Color':
        """Get a color from a string hex code, in format "#FFFFFF" """
        return Color(int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))

    @staticmethod
    def bit_string(i: int) -> 'Color':
        """conver the 24bit encoded int to tuple of R, G, and B.
           int bitmap encoded as GGGGGGGGRRRRRRRRBBBBBBBB"""
        r, g, b = int2tuple(i)
        return Color(r, g, b)

    @staticmethod
    def random(saturation: float = 1, lightness: float = 0.6) -> 'Color':
        """Generate a random color.
           The random value is for the Hue. The saturation and lightness can be specified"""
        return Color.hsl(random.random(), saturation, lightness)

    @staticmethod
    def different_from(color: 'Color') -> 'Color':
        """Generate a random color which is different from the color passed into it, maintaining the same hue and saturation"""
        h, s, v = colorsys.rgb_to_hsv(*color.to_tuple())
        newh = ((h * 360 + random.randint(0, 180) + 40) % 360) / 360
        nr, ng, nb = colorsys.hsv_to_rgb(newh, s, v)
        return Color(int(nr), int(ng), int(nb))

    @staticmethod
    def black() -> "Color":
        """The color black / off"""
        return Color(0, 0, 0)

    @staticmethod
    def red() -> "Color":
        """The color red"""
        return Color(255, 0, 0)

    @staticmethod
    def orange() -> "Color":
        """The color orange"""
        return Color(252, 81, 8)

    @staticmethod
    def amber() -> "Color":
        """The color amber"""
        return Color(251, 136, 10)

    @staticmethod
    def yellow() -> "Color":
        """The color yellow"""
        return Color(234, 163, 8)

    @staticmethod
    def lime() -> "Color":
        """The color lime"""
        return Color(107, 202, 3)

    @staticmethod
    def green() -> "Color":
        """The color green"""
        return Color(0, 255, 0)

    @staticmethod
    def emerald() -> "Color":
        """The color emeral"""
        return Color(23, 178, 106)

    @staticmethod
    def teal() -> "Color":
        """The color teal"""
        return Color(23, 175, 150)

    @staticmethod
    def cyan() -> "Color":
        """The color cyan"""
        return Color(21, 170, 210)

    @staticmethod
    def sky() -> "Color":
        """The color sky"""
        return Color(20, 146, 241)

    @staticmethod
    def blue() -> "Color":
        """The color blue"""
        return Color(0, 0, 255)

    @staticmethod
    def indigo() -> "Color":
        """The color indigo"""
        return Color(78, 64, 255)

    @staticmethod
    def violet() -> "Color":
        """The color violet"""
        return Color(122, 47, 255)

    @staticmethod
    def purple() -> "Color":
        """The color purple"""
        return Color(155, 30, 255)

    @staticmethod
    def fuchsia() -> "Color":
        """The color fuchia"""
        return Color(215, 0, 250)

    @staticmethod
    def pink() -> "Color":
        """The color pink"""
        return Color(240, 15, 137)

    @staticmethod
    def rose() -> "Color":
        """The color rose"""
        return Color(251, 0, 69)

    @staticmethod
    def white() -> "Color":
        """The color white"""
        return Color(255, 255, 255)

    @staticmethod
    def mix(a: "Color", b: "Color", x: float):
        """Mix two colors together
        
        args:
            a: The first color
            b: The second color
            x: the amount to mix by, 0.5 is average, 0 gives a, 1 gives b
        """
        return Color(
            int(a.r + (b.r - a.r) * x),
            int(a.g + (b.g - a.g) * x),
            int(a.b + (b.b - a.b) * x)
        )

    def to_tuple(self) -> tuple[int, int, int]:
        """Returns the tuple of the R, G and B, values between 0 and 255 """
        return (self._r, self._g, self._b)

    def to_hex(self) -> str:
        """to_hex Get the hex value of the current color

        Convert the current color to the hex value representing it and then return

        Returns:
            str: The current color in the format #RRGGBB
        """

        return tuple2hex((self._r, self._g, self._b))

    def to_hsl(self) -> tuple[float, float, float]:
        """Returns the HSL values of the color, between 0 and 1.0" """
        return colorsys.rgb_to_hls(self._r, self._g, self._b)

    def to_bit_string(self) -> int:
        """Return the color as an byte string integer, 
       int bitmap encoded as GGGGGGGGRRRRRRRRBBBBBBBB"""
        return (self._r << 8) | (self._g << 16) | self._b

    def on(self):
        """on Set the color to on

        Sets the color to the fully on state (white, RGB(255,255,255))
        
        Examples:
            ```py
            my_color = Color.red() # Creates a new color that is red
            my_color.on() # The color is now white (255,255,255)
            ```
        """
        self._r = 255
        self._g = 255
        self._b = 255

        self._changed = True

    def off(self):
        """off Set the color to off

        Sets the color to the fully off state (black, RGB(0,0,0))
        
        Examples:
            ```py
            my_color = Color.red() # Creates a new color that is red
            my_color.off() # The color is now black (0,0,0)
            ```
        """
        self._r = 0
        self._g = 0
        self._b = 0

        self._changed = True

    def fade(self, n: float = 1.1):
        """fade Fades a color

        Fade the color slightly n

        Args:
            n (float, optional): Controls the speed of the fade. The larger the number, the faster it will fade. Values less than 1 cause the color to get brighter to a max color of white. Defaults to 1.1.
        """
        
        self._r = int(clamp(self.r / n, 0, 255))
        self._g = int(clamp(self.g / n, 0, 255))
        self._b = int(clamp(self.b / n, 0, 255))

        self._changed = True


    def lerp(self, target: "Color", n: int, override: bool = False, fn: Callable[[float], float] = linear):
        """Linearly interpolate the color from its current color to the target color over n frames.
        
        Each successive call to lerp will advance the interpolation by a frame. After n amount of calls, it will be the target color. Any change to the target or frames amount will reset the interpolation from the current color. fn provides a way to choose an interpolation method, defaults to linear

        Examples:
            >>> my_color = Color.red() # (255, 0, 0)
            >>> my_color.lerp((0, 0, 0), 5) # (205, 0, 0)
            >>> my_color.lerp((0, 0, 0), 5) # (153, 0, 0)
            >>> my_color.lerp((0, 0, 0), 5) # (102, 0, 0)
            >>> my_color.lerp((0, 0, 0), 5) # (51, 0, 0)
            >>> my_color.lerp((0, 0, 0), 5) # (0, 0, 0)
            # once reacing the target, lerp has no effect
            >>> my_color.lerp((0, 0, 0), 5) # (0, 0, 0)

        """

        self.set_lerp(target, n, override, fn)
  
    def lerp_reset(self):
        """lerp_reset Reset to lerp step 0

        This method sets the previous lerp state to the current color, and sets the step number to 0
        """
        self._L_previous[0] = self.r
        self._L_previous[1] = self.g
        self._L_previous[2] = self.b

        self._L_step = 0

    def set_lerp(self, target: "Color", time: int, override: bool = False, fn: Callable[[float], float] = linear):
        """This resets the lerp and starts interpolation to target from current value. Successive calls will not change the target unless override is set to True. Use with cont_lerp to have the same effect as lerp()"""
        if (target.to_tuple() != self._L_target or self._L_total != time) or override:
            self.lerp_reset()
            self._L_target = target.to_tuple()
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



    def set(self, c: "Color"):
        """Set the color to another color by value"""
        self._r = c._r
        self._g = c._g
        self._b = c._b

        self._changed = True
        
    def set_color(self, c: "Color"):
        self._r = c._r
        self._g = c._g
        self._b = c._b

        self._changed = True
    
    def set_rgb(self, r: int, g: int, b: int):        
        """Set the red, green and blue values of the color, values between 0 and 255"""
        self._r = r & 0xff
        self._g = g & 0xff
        self._b = b & 0xff

        self._changed = True

    def set_hsl(self, hue: float, sat: float, lig: float):
        """Set the color via HSL, values between 0 and 1.0"""
        r, g, b = colorsys.hsv_to_rgb(hue, sat, lig)
        self._r = int(r * 255)
        self._g = int(g * 255)
        self._b = int(b * 255)

        self._changed = True

    def set_hex(self, s: str):
        """Set the color with a string hex code, in format "#FFFFFF" """
        self._r, self._g, self._b = int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16)

        self._changed = True

    def set_bit_string(self, i: int):
        """Set the color with a string hex code, in format "#FFFFFF" """
        self._r, self._g, self._b = int2tuple(i)

        self._changed = True

    def set_random(self, saturation: float = 1, lightness: float = 0.6):
        """Set the color to a random color.
           The random value is for the Hue. The saturation and lightness can be specified"""
        self.set_hsl(random.random(), saturation, lightness)

        self._changed = True

    def set_different_from(self, color: 'Color'):
        """Set the color to a random color which is different from the color passed into it, maintaining the same hue and saturation"""
        h, s, v = color.to_hsl()
        newh = ((h * 360 + random.randint(0, 180) + 40) % 360) / 360
        self.set_hsl(newh, s, v) # handles the changed and lerp reset

    def set_different_from_self(self):
        """Set the color to a random color which is different to the current color, maintaining the same hue and saturation"""
        h, s, v = self.to_hsl()
        newh = ((h * 360 + random.randint(0, 180) + 40) % 360) / 360
        self.set_hsl(newh, s, v) # handles the changed and lerp reset

    def set_black(self):
        self._r, self._g, self._b = 0, 0, 0
        self._changed = True

    def set_red(self):
        self._r, self._g, self._b = 255, 0, 0
        self._changed = True

    def set_orange(self):
        self._r, self._g, self._b = 252, 81, 8
        self._changed = True

    def set_amber(self):
        self._r, self._g, self._b = 251, 136, 10
        self._changed = True

    def set_yellow(self):
        self._r, self._g, self._b = 234, 163, 8
        self._changed = True

    def set_lime(self):
        self._r, self._g, self._b = 107, 202, 3
        self._changed = True

    def set_green(self):
        self._r, self._g, self._b = 0, 255, 0
        self._changed = True

    def set_emerald(self):
        self._r, self._g, self._b = 23, 178, 106
        self._changed = True

    def set_teal(self):
        self._r, self._g, self._b = 23, 175, 150
        self._changed = True

    def set_cyan(self):
        self._r, self._g, self._b = 21, 170, 210
        self._changed = True

    def set_sky(self):
        self._r, self._g, self._b = 20, 146, 241
        self._changed = True

    def set_blue(self):
        self._r, self._g, self._b = 0, 0, 255
        self._changed = True

    def set_indigo(self):
        self._r, self._g, self._b = 78, 64, 255
        self._changed = True

    def set_violet(self):
        self._r, self._g, self._b = 122, 47, 255
        self._changed = True

    def set_purple(self):
        self._r, self._g, self._b = 155, 30, 255
        self._changed = True

    def set_fuchsia(self):
        self._r, self._g, self._b = 215, 0, 250
        self._changed = True

    def set_pink(self):
        self._r, self._g, self._b = 240, 15, 137
        self._changed = True

    def set_rose(self):
        self._r, self._g, self._b = 251, 0, 69
        self._changed = True

    def set_white(self):
        self._r, self._g, self._b = 255, 255, 255
        self._changed = True



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

    def __init__(self, id: int, coord: tuple[float, float, float], tree: "Tree", color: Color = Color.black()):
        super().__init__(*color.to_tuple())
        self._id = id

        self._x = coord[0]
        self._y = coord[1]
        self._z = coord[2]

        self._a = math.atan2(self._y, self._x)
        self._d = math.sqrt(self._y ** 2 + self._x ** 2)
        
        self._tree = tree

    @property
    def id(self) -> int:
        """The id in the LED sequence"""
        return self._id

    @property
    def x(self) -> float:
        """The X coordinate, left (-1) to right (+1)"""
        return self._x

    @property
    def y(self) -> float:
        """The Y coordinate, front (+1) to back (-1)"""
        return self._y

    @property
    def z(self) -> float:
        """The Z coordinate bottom (0) to top (height())"""
        return self._z

    @property
    def xyz(self) -> tuple[float, float, float]:
        """The tuple containing the xyz coordinates"""
        return (self._x, self._y, self._z)

    @property
    def a(self) -> float:
        """The angle clockwise from the x+ direction around the tree"""
        return self._a

    @property
    def d(self) -> float:
        """The distance from the center line (trunk) of the tree"""
        return self._d

    def distance_to(self, p: "Pixel") -> float:
        """Find the distance to the passed pixel
        example:
            ```
            my_pixel = pixels(0)
            print(my_pixel.distance_to(pixels(10))) # 0.45
        """
        return self._tree._distances[self._id][p.id]

    def nearest(self, n: int) -> list[tuple["Pixel", float]]:
        """Find the nearest n pixels from the current

            example:
                ```
                my_pixel = pixels(0)
                neighbors = my_pixel.nearest(4)
                len(neighbors) # 4, nearest pixels
                ```
        """
        return self._tree._pixel_distance_matrix[self._id][:n]

    def within(self, d: float) -> list["Pixel"]:
        """Find all pixels that are within a certain radius

            example:
                ```
                my_pixel = pixels(0)
                neighbors = my_pixel.within(0.4) # pixels within 0.4 radius
                ```
        """
        left = 0
        right = self._tree._num_pixels - 1
        while left < right:
            mid = (left + right) // 2
            if self._tree._pixel_distance_matrix[self._id][mid][1] < d:
                left = mid + 1
            else:
                right = mid
        return list(map(lambda x: x[0], self._tree._pixel_distance_matrix[self._id][:left]))

def int2tuple(c: int) -> tuple[int, int, int]:
    """conver the 24bit encoded int to tuple of R, G, and B.
       int bitmap encoded as GGGGGGGGRRRRRRRRBBBBBBBB"""
    return ((c >> 8) & 0xff, (c >> 16) & 0xff, c & 0xff)

def tuple2int(t: tuple[int, int, int]) -> int:
    """conver rgb to 24bit encoded int.
       int bitmap encoded as GGGGGGGGRRRRRRRRBBBBBBBB
    """
    return (t[0] << 8) | (t[1] << 16) | t[2]


def tuple2hex(t: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to hex string """
    return '#%02x%02x%02x' % t


def hex2tuple(h: str) -> tuple[int, int, int]:
    """Convert a hex string to an RGB tuple"""
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

if __name__ == "__main__":
    red = Color.red()

    c = Color.black()
    red.lerp(c, 5)
    if red.to_tuple() != (204, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp(c, 5)
    if red.to_tuple() != (153, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp(c, 5)
    if red.to_tuple() != (102, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp(c, 5)
    if red.to_tuple() != (50, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp(c, 5)
    if red.to_tuple() != (0, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")

    red.lerp(c, 5)
    if red.to_tuple() != (0, 0, 0):
        print(red.to_tuple())
        raise Exception("lerp wrong")
