import pygame.locals as PLocals
import pygame
import OpenGL.GL as GL
import OpenGL.GLU as GLU
import OpenGL.GLUT as GLUT
import csv

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
        self.setup_visualisation()

    def setup_visualisation(self):
        pygame.init()
        display = (800, 600)
        pygame.display.set_mode(display, PLocals.DOUBLEBUF | PLocals.OPENGL)
        GLU.gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
        GL.glRotate(-80, 0, 0, 0)
        GL.glTranslatef(0, 8, -3)

        self.clock = pygame.time.Clock()

    def draw_light(self, position, color):
        GL.glColor3fv((max(40/255, color[1]/255), max(40/255, color[2]/255), max(40/255, color[0]/255)))
        GL.glPushMatrix()
        GL.glTranslate(position[0], position[1], position[2])
        GLUT.glutSolidSphere(0.02, 10, 10)
        GL.glPopMatrix()

    def show(self):
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        for coord, color in zip(self.coords, self.pixels):
            self.draw_light(coord, color)

        pygame.display.flip()
        self.clock.tick(60)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

    def __getitem__(self, index):
        return self.pixels[index]

    def __setitem__(self, index, item):
        self.pixels[index] = item

    def __len__(self):
        return self.num
