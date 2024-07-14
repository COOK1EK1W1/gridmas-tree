import pygame.locals as PLocals
import pygame
import OpenGL.GL as GL
import OpenGL.GLU as GLU
import csv
import time


def read_csv():
    with open("tree.csv") as csvfile:
        reader = csv.reader(csvfile)
        list_of_lists = [[float(item) for item in row] for row in reader]
    return list_of_lists


class SimTree:
    def __init__(self):
        self.coords = read_csv()
        self.num = len(self.coords)
        self.pixels = [(0, 0, 0) for _ in range(self.num)]
        self.buffer = [(0, 0, 0) for _ in range(self.num)]

    def setup_visualisation(self):
        pygame.init()
        display = (800, 600)
        pygame.display.set_mode(display, PLocals.DOUBLEBUF | PLocals.OPENGL)
        GL.glMatrixMode(GL.GL_PROJECTION)
        display = (800, 600)
        GLU.gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
        GL.glTranslatef(0, -1, -5)
        GL.glRotatef(-60, 1, 0, 0)
        GL.glMatrixMode(GL.GL_MODELVIEW)

    def run(self):
        self.setup_visualisation()
        while True:
            time.sleep(1 / 30)
            self._show()

    def draw_light(self, position, color):
        GL.glPointSize(5)
        GL.glBegin(GL.GL_POINTS)
        GL.glColor3f(color[0] / 255, color[1] / 255, color[2] / 255)  # Set the color for the point

        # Draw the point at the specified position
        GL.glVertex3f(position[0], position[1], position[2])

        GL.glEnd()
        error = GL.glGetError()

        if error != GL.GL_NO_ERROR:
            print(GL.glGetError())

    def _show(self):
        GL.glRotatef(-1, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        for coord, color in zip(self.coords, self.buffer):
            self.draw_light(coord, color)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

    def show(self):
        self.buffer = [x for x in self.pixels]

    def __getitem__(self, index):
        return self.pixels[index]

    def __setitem__(self, index, item):
        self.pixels[index] = item

    def __len__(self):
        return self.num
