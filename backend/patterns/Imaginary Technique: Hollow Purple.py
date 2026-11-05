import random
import math

from gridmas import *

name = "Imaginary Technique: Hollow Purple"
author = "Ross Brown"
'''
have blue for 300 ticks X
introduce red with offset movements X
have them sync up (red set to angle 1 and 2)
speed up
make purple
explode


'''
cur_height = 0.5
angle = random.randrange(0, 1000) / 100
angle2 = random.randrange(0, 200) / 100
angle3 = random.randrange(0, 1000) / 100
angle4 = random.randrange(0, 200) / 100


i=0
dist = 0.5
radius = RangeAttr("radius", 0.4, 0.1, 0.8, 0.03)
color = ColorAttr("ball color", Color.blue())

#purple = ColorAttr("ball color", Color.purple())
trailLength = RangeAttr("Trail Length", 10, 5, 20, 5)

def draw():
    global angle, cur_height, angle2, dist,i,radius,blue,red,purple, angle3,angle4
    ### Hollow Purple
    i+=1
    if i > 700:
        radius = RangeAttr("radius", 0.4, 0.3, 0.8, 0.03)
        lerp(Color.black(), int(trailLength.get()))

        angle = (angle + 0.351) % 6.28
        angle2 = (angle2 + 0.034) % 6.28

        center = [dist * math.sin(angle), dist * math.cos(angle), cur_height]
        cur_height = abs(math.sin(angle2)) * (height() - radius.get() * 2) + radius.get()
        Sphere((center[0], center[1], cur_height), radius.get(), Color.purple())
        if i > 1000:
            for pixel in pixels():
                pixel.set_color(Color.purple())
        if i > 1100:
            i = 0
    else:
        ### amplification, blue
        lerp(Color.black(), int(trailLength.get()))

        angle = (angle + 0.1) % 6.28
        angle2 = (angle2 + 0.004) % 6.28

        center = [dist * math.sin(angle), dist * math.cos(angle), cur_height]
        cur_height = abs(math.sin(angle2)) * (height() - radius.get() * 2) + radius.get()
        Sphere((center[0], center[1], cur_height), radius.get(), color.get())
        

        if i % 20 == 0:
            print(i)
        ### Reversal red
        if i > 200:
            lerp(Color.black(), int(trailLength.get()))

            if i > 400:
                angle = (angle + 0.21) % 6.28
                angle2 = (angle2 + 0.034) % 6.28
                angle3 = (angle + 0.21) % 6.28
                angle4 = (angle2 + 0.034) % 6.28
            else:
                angle3 = (angle3 + 0.11) % 6.28
                angle4 = (angle4 + 0.034) % 6.28

            center = [dist * math.cos(angle3), dist * math.sin(angle3), cur_height]
            cur_height = abs(math.sin(angle4)) * (height() - radius.get() * 2) + radius.get()
            Sphere((center[0], center[1], cur_height), radius.get(),Color.red())
