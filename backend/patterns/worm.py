import random
from attribute import RangeAttr, ColorAttr
from tree import tree
from colors import Color


name = "Worm"  

author = "guilhem"


def run():

   listPixel = []

   while True:

       tree.fill(Color.green())     

       for pixel  in tree.pixels:

           tree.sleep(True)

           if(len(listPixel) == 30):

               p = listPixel.pop(0)

               p.set_rgb(0, 0, 0)

           pixel.set_rgb(0, 0, 255)

           listPixel.append(pixel)

       tree.update()
