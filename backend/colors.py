from os import times_result
import random
import time
import colorsys


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


def clamp(val: float | int, minv: float | int, maxv: float | int):
    return min(max(val, minv), maxv)


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r: int = r & 0xff
        self.g: int = g & 0xff
        self.b: int = b & 0xff

        self._L_previous = (0, 0, 0)
        self._L_target = (0, 0, 0)

        self._L_step = 0
        self._L_total = 1

    def set_RGB(self, r: int, g: int, b: int):
        self.r = r & 0xff
        self.g = g & 0xff
        self.b = b & 0xff

        self.lerp_reset()

    def set_color(self, color: 'Color'):
        self.set_RGB(*color.toTuple())

    def fade(self, n: float = 1.1):
        self.r = int(clamp(self.r / n, 0, 255))
        self.g = int(clamp(self.g / n, 0, 255))
        self.b = int(clamp(self.b / n, 0, 255))

        self.lerp_reset()

    def toHex(self) -> str:
        return tuple2hex((self.r, self.g, self.b))

    def toTuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def lerp_reset(self):
        self._L_previous = (self.r, self.g, self.b)
        self._L_step = 0

    def lerp(self, target: tuple[int, int, int], time: int):
        if target != self._L_target or self._L_total != time:
            self.lerp_reset()
            self._L_target = target
            self._L_total = time
        else:
            percent = self._L_step / self._L_total
            self.r = int(self._L_previous[0] * (1 - percent) + self._L_target[0] * percent)
            self.g = int(self._L_previous[1] * (1 - percent) + self._L_target[1] * percent)
            self.b = int(self._L_previous[2] * (1 - percent) + self._L_target[2] * percent)
            self._L_step += 1

    @staticmethod
    def fromHex(s: str) -> 'Color':
        return Color(int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))

    @staticmethod
    def fromHSL(hue: float, sat: float, lig: float) -> 'Color':
        r, g, b = colorsys.hsv_to_rgb(hue, sat, lig)
        return Color(int(r * 255), int(g * 255), int(b * 255))

    @staticmethod
    def white() -> 'Color':
        return Color(255, 255, 255)

    @staticmethod
    def black() -> 'Color':
        return Color(0, 0, 0)

    @staticmethod
    def red() -> 'Color':
        return Color(255, 0, 0)

    @staticmethod
    def green() -> 'Color':
        return Color(0, 255, 0)

    @staticmethod
    def blue() -> 'Color':
        return Color(0, 0, 255)

    @staticmethod
    def random(saturation: float = 1, lightness: float = 0.7) -> 'Color':
        return Color.fromHSL(random.random(), saturation, lightness)

    @staticmethod
    def differentfrom(color: 'Color') -> 'Color':
        h, s, v = colorsys.rgb_to_hsv(*color.toTuple())
        newh = ((h * 360 + random.randint(0, 180) + 40) % 360) / 360
        nr, ng, nb = colorsys.hsv_to_rgb(newh, s, v)
        return Color(int(nr), int(ng), int(nb))


def tuple2hex(c: tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % c


def hex2tuple(h: str) -> tuple[int, int, int]:
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
    a = time.perf_counter()
    for i in range(10_000_000):
        newColor = Color(1, 2, 3)
        newColor.set_RGB(3, 2, 1)
        newColor.fade()
    print(time.perf_counter() - a)
