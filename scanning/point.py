# create a class of points
import cv2

# 0, 1 for landscape; 1, 0 for portrait
z_dir = 0
horiz_dir = 1


class Point:
    def __init__(self, index: int, paths: list[str], dirs: list[int]):
        self.index = index
        self.paths = paths
        self.dirs = dirs
        self.locs = [imageBP(x) for x in paths]

    def getZ(self):
        locs: list[int] = []
        weights: list[float] = []
        for location in self.locs:
            _, maxVal, _, maxLoc = location
            locs.append(maxLoc[z_dir])
            weights.append(maxVal)
        temp: list[float] = []
        for i in range(len(locs)):
            temp.append(locs[i] * weights[i])

        return int(sum(temp) / sum(weights)) - 400

    def getY(self, centers: list[int]):
        locs: list[int] = []
        weights: list[float] = []
        for dirI, (dir, loc) in enumerate(zip(self.dirs, self.locs)):
            _, maxVal, _, maxLoc = loc
            if dir == 0:
                locs.append(maxLoc[horiz_dir] - centers[0])
                weights.append(maxVal)
            elif dir == 180:
                locs.append(get_dim(self.paths[dirI])[
                    horiz_dir] - maxLoc[horiz_dir] - centers[2])
                weights.append(maxVal)
            elif dir == 90:
                continue
            elif dir == 270:
                continue

        temp: list[float] = []
        for i in range(len(locs)):
            temp.append(locs[i] * weights[i])

        if len(temp) == 0:
            return 0
        else:
            result = int(sum(temp) / sum(weights))
            return result

    def getX(self, centers: list[int]):
        locs: list[int] = []
        weights: list[float] = []
        for dirI in range(len(self.dirs)):
            _, maxVal, _, maxLoc = self.locs[dirI]
            if self.dirs[dirI] == 0:
                continue
            elif self.dirs[dirI] == 180:
                continue
            elif self.dirs[dirI] == 90:
                locs.append(maxLoc[horiz_dir] - centers[1])
            elif self.dirs[dirI] == 270:
                locs.append(get_dim(self.paths[dirI])[
                            horiz_dir] - maxLoc[horiz_dir] - centers[3])
            weights.append(maxVal)

        temp: list[float] = []
        for i in range(len(locs)):
            temp.append(locs[i] * weights[i])

        if len(temp) == 0:
            return 0
        else:

            return int(sum(temp) / sum(weights))

    def getPosForDir(self, dir: int):
        return self.locs[self.dirs.index(dir)]


def imageBP(fp: str):
    image = cv2.imread(fp)
    orig = image.copy()
    gray = cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY)
    # gray = cv2.GaussianBlur(gray, (blurAmount, blurAmount), 0)
    minVal, maxVal, minLoc, maxLoc = cv2.minMaxLoc(gray)
    # cv2.circle(gray, maxLoc, 6, (255, 0, 0), 3)
    # cv2.imshow('image', gray)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    # print(maxLoc)
    return minVal, maxVal, minLoc, maxLoc


def get_dim(fp: str):
    (x, y, z) = cv2.imread(fp).shape
    return (y, x, z)
