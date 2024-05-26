from colors import Color

class Pixel(Color):
    def __init__(self, coord: tuple[float, float, float],color: Color = Color.black()):
        super().__init__(*color.toTuple())
        self.x = coord[0]
        self.y = coord[1]
        self.z = coord[2]
