from gridmas import *
import random



name = "Jumpy Balls"
author = "Ciaran"

class Ball:
    def __init__(self):

        self.c = Color.random()
        self.x = random.random() - 0.5
        self.y = random.random() - 0.5
        self.z = height()
        self.xVel = (random.random() - 0.5) * 0.3
        self.yVel = (random.random() - 0.5) * 0.3
        self.zVel = (1 - random.random()) * 0.03





def draw():
    balls = []

    
    while True:
        balls.append(Ball())
        if len(balls) > 5:
            balls.pop(0)
        for _ in range(random.randrange(50, 100)):
            lerp(Color(0, 0, 0), 5)
            for ball in balls:
                Sphere((ball.x, ball.y, ball.z), 0.2, ball.c)

                ball.zVel -= 0.03
                ball.z += ball.zVel
                ball.x += ball.xVel
                ball.y += ball.yVel

                if ball.z < 0:
                    ball.zVel *= -0.9
                    ball.z = 0.1
                if ball.x > 0.8 or ball.x < -0.8:
                    ball.xVel *= -0.9
                    ball.yVel += (random.random() - 0.5) * 0.1
                if ball.y > 0.8 or ball.y < -0.8:
                    ball.yVel *= -0.9
                    ball.xVel += (random.random() - 0.5) * 0.1

            yield
