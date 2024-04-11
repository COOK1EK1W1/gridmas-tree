from util import tree
import time
import math

# Play with these values to change how coarse the plasma effect is.
# Smaller value == faster
MATWX = 20
MATWY = 20
MATWZ = 60

# Set this value to lower the RGB (1 = full range, 0.5 = Half range, etc...)
dimLight = 0.8

class boundingBox():
    def __init__(self):
        self.minX = math.inf
        self.maxX = -math.inf
        self.minY = math.inf
        self.maxY = -math.inf
        self.minZ = math.inf
        self.maxZ = -math.inf
        self.wX = 0
        self.wY = 0
        self.wZ = 0

    def update(self, x, y, z):
        if self.minX > x:
            self.minX = x
        if self.maxX < x:
            self.maxX = x

        if self.minY > y:
            self.minY = y
        if self.maxY < y:
            self.maxY = y

        if self.minZ > z:
            self.minZ = z
        if self.maxZ < z:
            self.maxZ = z

    def finalize(self):
        self.wX = self.maxX - self.minX
        self.wY = self.maxY - self.minY
        self.wZ = self.maxZ - self.minZ

    def normalize(self, x, y, z):
        lx = (x - self.minX) / self.wX
        ly = (y - self.minY) / self.wY
        lz = (z - self.minZ) / self.wZ
        return lx, ly, lz


class matrix():
    def __init__(self, lx, ly, lz, bb):
        self._list = []
        for i in range(lx * ly * lz):
            self._list.append([0, 0, 0])

        self._strideX = 1
        self._strideY = self._strideX * lx
        self._strideZ = self._strideY * ly
        self._bb = bb
        self._wX = lx
        self._wY = ly
        self._wZ = lz

    def get(self, x, y, z):
        return self._list[x * self._strideX + y * self._strideY + z * self._strideZ]

    def set(self, x, y, z, val):
        self._list[x * self._strideX + y * self._strideY + z * self._strideZ] = val

    def getTree(self, x, y, z):
        localX, localY, localZ = self._bb.normalize(x, y, z)
        localX = int(localX * (self._wX - 1))
        localY = int(localY * (self._wY - 1))
        localZ = int(localZ * (self._wZ - 1))
        return self.get(localX, localY, localZ)


def dist(x, y, z, wx, wy, wz):
    return math.sqrt((x - wx) * (x - wx) + (y - wy) * (y - wy) + (z - wz) * (z - wz))


name = "threeDPlasma"
display_name = "3D Plasma"


def run():

    treeBB = boundingBox()
    for i in tree.coords:
        treeBB.update(i[0], i[1], i[2])

    treeBB.finalize()

    workMat = matrix(MATWX, MATWY, MATWZ, treeBB)

    slow = 0

    t = 0

    while True:

        time.sleep(slow)

        for LED in range(0, tree.num_pixels):
            tree.pixels[LED] = workMat.getTree(tree.coords[LED][0], tree.coords[LED][1], tree.coords[LED][2])

        tree.update()

        # Update the matrix
        for x in range(0, MATWX):
            for y in range(0, MATWY):
                for z in range(0, MATWZ):
                    d1 = dist(x + t, y, z, MATWX, MATWY, MATWZ)
                    d2 = dist(x, y, z,  MATWX/2, MATWY/2, MATWZ)
                    d3 = dist(x, y + t / 7, z, MATWX * 0.75, MATWY/2, MATWZ)
                    d4 = dist(x, y, z, MATWX*0.75, MATWY, MATWZ)

                    value = math.sin(d1 / 8) + math.sin(d2 / 8.0) + math.sin(d3 / 7.0) + math.sin(d4 / 8.0)

                    colour = int((4 + value)) * 32
                    r = min(colour, 255) * dimLight
                    g = min(colour * 2, 255) * dimLight
                    b = min(255 - colour, 255) * dimLight

                    workMat.set(x, y, z, (g, r, b))
        t = t + 1

