
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


class Color:
    def __init__(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    def toHex(self) -> str:
        return tuple2hex((self.r, self.g, self.b))

    def toTuple(self) -> tuple[int, int, int]:
        return (self.r, self.g, self.b)

    @staticmethod
    def fromHex(s: str) -> 'Color':
        return Color(int(s[1:3], 16), int(s[3:5], 16), int(s[5:7], 16))

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


def tuple2hex(c: tuple[int, int, int]) -> str:
    return '#%02x%02x%02x' % c


def hex2tuple(h: str) -> tuple[int, int, int]:
    return (int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16))


def hsl_to_rgb(hue, sat, lit):
    """
    Convert HSL (Hue, Saturation, Lightness) to RGB (Red, Green, Blue).
    All input values should be in the range [0, 1].
    """
    if sat == 0:
        # Achromatic (gray)
        return int(lit * 255), int(lit * 255), int(lit * 255)
    else:
        def hue_to_rgb(p, q, t):
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1 / 6:
                return p + (q - p) * 6 * t
            if t < 1 / 2:
                return q
            if t < 2 / 3:
                return p + (q - p) * (2 / 3 - t) * 6
            return p

        q = lit * (1 + sat) if lit < 0.5 else lit + sat - lit * sat
        p = 2 * lit - q
        r = hue_to_rgb(p, q, hue + 1 / 3)
        g = hue_to_rgb(p, q, hue)
        b = hue_to_rgb(p, q, hue - 1 / 3)

        return int(r * 255), int(g * 255), int(b * 255)


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
    print(list(tests2))
