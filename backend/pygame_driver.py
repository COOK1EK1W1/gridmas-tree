"""A PixelDriver that displays frames in a pygame/OpenGL window instead of sending them
to a physical tree. Useful for local development when no hardware is attached.

Kept in its own module (rather than pixel_driver.py) so that pygame/PyOpenGL are only
required when this driver is actually used.
"""

import os

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', "hide")

import time
from collections import deque

import numpy as np
import pygame
import pygame.locals as PLocals
import OpenGL.GL as GL
import OpenGL.GLU as GLU

from pixel_driver import PixelDriver


class PygamePixelDriver(PixelDriver):
    """Simulates the tree in a pygame window.

    Frames are generated ahead of real time (see PREROLL/BUFFER in PixelDriver), so
    flush() cannot just draw the frame it's given immediately - it stashes each
    incoming frame in a buffer tagged with the time it's meant to be shown, and
    displays whichever buffered frame has become due whenever it's called.
    """

    def __init__(self, pixel_count: int, name: str, fps: int, window_size: tuple[int, int] = (800, 600)):
        super().__init__(pixel_count, name, fps)
        self._window_size = window_size
        self._coords: list[tuple[float, float, float]] | None = None
        self._frame_buffer: deque[tuple[float, np.ndarray]] = deque()
        self._display_ready = False
        self._closed = False

    def _init_display(self):
        pygame.init()
        pygame.display.set_mode(self._window_size, PLocals.DOUBLEBUF | PLocals.OPENGL)
        pygame.display.set_caption(self.name)

        GL.glMatrixMode(GL.GL_PROJECTION)
        GLU.gluPerspective(45, (self._window_size[0] / self._window_size[1]), 0.1, 50.0)
        GL.glTranslatef(0, -1, -5)
        GL.glRotatef(-60, 1, 0, 0)
        GL.glMatrixMode(GL.GL_MODELVIEW)

        self._display_ready = True

    def flush(self, frame, t: float):
        if self._closed:
            return

        if not self._display_ready:
            self._init_display()

        if self._coords is None:
            self._coords = [c for fixture, _ in self.fixtures for c in fixture._coords]

        if self.fixtures:
            rgb = np.concatenate([fixture._rgb for fixture, _ in self.fixtures])
        else:
            rgb = np.zeros((0, 3), dtype=np.uint8)

        self._frame_buffer.append((t, frame.copy()))

        self._pump_events()
        self._play_due_frames()

    def _pump_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                self._closed = True

    def _play_due_frames(self):
        if self._closed:
            return

        now = time.time()
        due_frame = None
        # if we've fallen behind, skip straight to the newest due frame instead of
        # burning through the backlog one at a time
        while self._frame_buffer and self._frame_buffer[0][0] <= now:
            due_frame = self._frame_buffer.popleft()

        if due_frame is None:
            return

        _, rgb = due_frame
        self._render(rgb)

    def _render(self, rgb: np.ndarray):
        assert self._coords is not None

        GL.glRotatef(-1, 0, 0, 1)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        GL.glPointSize(5)
        GL.glBegin(GL.GL_POINTS)
        for (x, y, z), (r, g, b) in zip(self._coords, rgb):
            GL.glColor3f(r / 255, g / 255, b / 255)
            GL.glVertex3f(x, y, z)
        GL.glEnd()

        pygame.display.flip()
