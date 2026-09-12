"""A `Strip` (see ../common/scheduler.py) that renders into a pygame/OpenGL
window instead of driving real hardware.

Lets a `device/pygame/simulate.py` process stand in for a physical device - it
speaks the exact same network pixel protocol (../common/app.py,
../common/scheduler.py), so a NetworkPixelDriver on the controller can't tell
the two apart. Run as many instances as you like, each with its own --port, to
simulate several devices/fixtures at once.

pygame/OpenGL calls must happen on the thread that created the window, but
frames arrive on FrameScheduler's own thread - render() therefore just stashes
the latest frame; run() (called from the main thread) picks it up and draws it.
"""

import os

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")

import threading
from typing import List, Tuple

import OpenGL.GL as GL
import OpenGL.GLU as GLU
import pygame
import pygame.locals as PLocals


class SimStrip:
    """Draws whatever frame was last given to render(), in a pygame window."""

    def __init__(self, coords: List[Tuple[float, float, float]], name: str = "gridmas-sim",
                 window_size: Tuple[int, int] = (800, 600)):
        self.pixel_count = len(coords)
        self._coords = coords
        self._name = name
        self._window_size = window_size

        self._lock = threading.Lock()
        self._pending = bytes(self.pixel_count * 3)
        self._dirty = False
        self.closed = False

    def render(self, rgb: bytes):
        with self._lock:
            self._pending = rgb
            self._dirty = True

    def clear(self):
        self.render(bytes(self.pixel_count * 3))

    def run(self):
        """Open the window and block, drawing frames as they arrive, until it's closed."""
        pygame.init()
        pygame.display.set_mode(self._window_size, PLocals.DOUBLEBUF | PLocals.OPENGL)
        pygame.display.set_caption(self._name)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GLU.gluPerspective(45, self._window_size[0] / self._window_size[1], 0.1, 50.0)
        GL.glTranslatef(0, -1, -5)
        GL.glRotatef(-60, 1, 0, 0)
        GL.glMatrixMode(GL.GL_MODELVIEW)

        clock = pygame.time.Clock()
        try:
            while not self.closed:
                if any(e.type == pygame.QUIT for e in pygame.event.get()):
                    self.closed = True
                    break

                with self._lock:
                    frame, dirty, self._dirty = self._pending, self._dirty, False
                if dirty:
                    self._draw(frame)

                clock.tick(60)
        finally:
            pygame.quit()

    def _draw(self, rgb: bytes):
        GL.glRotatef(-1, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glPointSize(5)
        GL.glBegin(GL.GL_POINTS)
        for i, (x, y, z) in enumerate(self._coords):
            GL.glColor3f(rgb[i * 3] / 255, rgb[i * 3 + 1] / 255, rgb[i * 3 + 2] / 255)
            GL.glVertex3f(x, y, z)
        GL.glEnd()
        pygame.display.flip()
