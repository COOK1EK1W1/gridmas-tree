import os

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
from multiprocessing import Queue
from colors import int2tuple
from typing import Optional
import pygame.locals as PLocals
import pygame
import OpenGL.GL as GL
import OpenGL.GLU as GLU
from pixel_driver.pixel_driver import PixelDriver


class SimTree(PixelDriver):
    def __init__(self, queue: "Queue[Optional[tuple[int, list[int]]]]", coords: list[tuple[float, float, float]]):
        super().__init__(queue, coords)
        self.buffer = [0 for _ in range(len(coords))]
        self.queue = queue

    def init(self):
        self.setup_visualisation()

    def draw(self, frame: list[int]):
        self.buffer = frame

    def show(self):
        self.pygame_frame()

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

    def pygame_frame(self):
        if len(self.coords) == 0:
            return

        GL.glRotatef(-1, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        GL.glPointSize(5)
        GL.glBegin(GL.GL_POINTS)

        for (x, y, z), color in zip(self.coords, self.buffer):
            r, g, b = int2tuple(color)
            GL.glColor3f(r / 255, g / 255, b / 255)  # Set the color for the point

            # Draw the point at the specified position
            GL.glVertex3f(x, y, z)


            """
            error = GL.glGetError()
            if error != GL.GL_NO_ERROR:
                print(GL.glGetError())
            """
        GL.glEnd()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return True