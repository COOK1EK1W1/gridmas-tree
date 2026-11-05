from gridmas import *
import math


red=Color(255,0,0)
white=Color(255,255,255)
green=Color(0,255,0)
yellow=Color(255,255,0)


class Point:
    def __init__(self,x,y):
        self.x=x
        self.y=y


def set_cylinder_xz(point,radius,col):
    for p in pixels():
        x=((p.x-point.x)*(p.x-point.x))
        y=((p.z-point.y)*(p.z-point.y))

        if x + y  < radius: 
            p.set_color(col)


'''
    if 0 is (0,1)
    pi is (0,-1)

'''

def set_arc_xz(point,radius,col,width,a,b):
    for p in pixels():
        x=((p.x-point.x)*(p.x-point.x))
        y=((p.z-point.y)*(p.z-point.y))

        if x + y  < radius and x + y > (radius - width): 
            p.set_color(col)

    
    
    #TODO create an arc 
    pass
                

class Grinch:
    def __init__(self):
        hatTop=[]
        hat=[]
        face=[]

        for p in pixels():
            if p.z > 3.2:
                hatTop.append(p)
                p.set_color(white)
            elif p.z > 2.2:
                hat.append(p)
                p.set_color(red)
            else:
                face.append(p)
                p.set_color(green)
            pass


        eye1=Point(0.4,1.1)
        eye2=Point(-0.4,1.1)
        set_cylinder_xz(eye1,0.07,yellow)
        set_cylinder_xz(eye2,0.07,yellow)
        
        set_cylinder_xz(eye1,0.01,Color(0,0,255))
        set_cylinder_xz(eye2,0.01,Color(0,0,255))


        




def reset_tree():
    for p in pixels():
        p.set_color(Color(0,0,0))

def draw():
    reset_tree()

    g=Grinch()
    pass


