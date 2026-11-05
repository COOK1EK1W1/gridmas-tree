import time
import math
import random
from gridmas import *

set_fps(60)
random.seed(time.time())

balls = []
delta = 1/60
radius = 0.5
speed = 0.5
g = 0.98

floor = 0.5

last_pos = (0, 0, floor)
last_vel = (0, 0.1, 1)

delay = 30

background(Color(15, 30, 10))

curr_time = time.time()


#vector functions
def dot(a, b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def norm(v):
    return math.sqrt(dot(v, v))

def normalize(v):
    n = norm(v)
    if n == 0:
        return v
    return (v[0]/n, v[1]/n, v[2]/n)

def minus(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])

def plus(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

def scale(v, s):
    return (v[0]*s, v[1]*s, v[2]*s)


class Ball:
    def __init__(self, pos, vel):
        self.pos = pos
        self.vel = vel
        self.color = Color.random()

    #moves the ball by velocity*delta
    def move(self):
        self.vel = (self.vel[0], self.vel[1], self.vel[2] - g * delta)
        self.pos = (self.pos[0] + self.vel[0] * delta,
        self.pos[1] + self.vel[1] * delta,
        self.pos[2] + self.vel[2] * delta)

def spawn_ball():
    global balls, last_pos, last_vel

    balls.append(Ball(last_pos, last_vel))
    #picks a random position that won't make the new ball overlap with others
    pos = (random.random(), random.random(), floor + random.random() * (height() - floor - radius))
    overlap = True
    while (overlap):
        overlap = False
        for ball in balls:
            if norm(minus(ball.pos, pos))<=radius * 2:
                overlap = True
                break
        pos = (random.random(), random.random(), floor + random.random() * (height() - floor - radius))
    #picks a random direction
    vel = normalize((random.random() - pos[0] * 1.8, random.random() - pos[1] * 1.8, random.random() - 0.5))
    vel = scale(vel, speed)

    last_pos = pos
    last_vel = vel


def draw():
    global curr_time, balls, delta

    #draws lines
    if frame()%100<=delay:
        t = (frame()%100)/(delay)
        v = (4 * t) ** 3 * (1 - t) ** 3
        Line(minus(last_pos, scale(last_vel,  200 * delta)),
            plus(last_pos, scale(last_vel,  200 * delta)),
            clamp(0.25 * v, 0.05, 0.25), Color(clamp(int(v * 210), 20, 255), 20, 10))

    #spawns balls
    if frame()%100==delay:
        spawn_ball()

    counter = 0
    for ball in balls:
        counter += 1
        for ball2 in balls[counter:]:
            overlap = radius * 2 - norm(minus(ball.pos, ball2.pos))
            if overlap>=0:
                # direction from ball to ball2
                n = normalize(minus(ball2.pos, ball.pos))

                # relative velocity
                rv = minus(ball.vel, ball2.vel)
                vel_along_normal = dot(rv, n)

                # if separating, skip
                if vel_along_normal > 0:
                    continue

                # elastic collision
                dv = scale(n, vel_along_normal)
                ball.vel  = minus(ball.vel, dv)
                ball2.vel = plus(ball2.vel, dv)

                # positional correction (half each)
                corr = scale(n, overlap * 0.5)
                ball.pos  = minus(ball.pos, corr)
                ball2.pos = plus(ball2.pos, corr)

        #deletion bounds
        if ball.pos[0]>=1.0 or ball.pos[0]<=-1.0 or ball.pos[1]>=1.0 or ball.pos[1]<=-1.0:
            balls.remove(ball)

        #bounce bounds
        if ball.pos[2]<=floor:
            ball.vel = (ball.vel[0], ball.vel[1], -ball.vel[2])
            ball.pos = (ball.pos[0], ball.pos[1], floor)
        elif ball.pos[2]>=height() - radius:
            ball.vel = (ball.vel[0], ball.vel[1], -ball.vel[2])
            ball.pos = (ball.pos[0], ball.pos[1], height())

        ball.move()
        Sphere(ball.pos, radius, ball.color)

    #updates the time
    delta = time.time() - curr_time
    curr_time = time.time()

