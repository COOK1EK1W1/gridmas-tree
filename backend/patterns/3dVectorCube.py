from tree import tree
from particle_system import ParticleSystem
from particle_system import SphereParticle
from attribute import RangeAttr
from colors import Color
import random
import math
name = "3D Vector Cube 🧊"
author = "Alex Howe"

class Sphere(SphereParticle):
    def __init__(self, x, y, z, radius, color):
        super().__init__(x, y, z, radius, 300, color)

    #(dummy)
    def advance(self):
        return

#Define 3D object
class Object:
        def __init__(self, axis, nodes, vectors, vectorcolours, nodecolour):
                self.nodex = []
                self.nodey = []
                self.nodez = []
                self.vector1 = []
                self.vector2 = []
                self.vectorcolours = vectorcolours
                self.nodecolour = nodecolour
                self.rotx = 0
                self.roty = 0
                self.axis = axis
                for i in range(len(nodes)):
                        self.nodex.append(nodes[i][0])
                        self.nodey.append(nodes[i][1])
                        self.nodez.append(nodes[i][2])
                for i in range(len(vectors)):
                        self.vector1.append(vectors[i][0])
                        self.vector2.append(vectors[i][1])

        #Move all nodes towards or away from axis by amount
        def changesize(self, amount):
            for i in range(len(self.nodex)):
                dx = self.nodex[i] - self.axis[0]
                dy = self.nodey[i] - self.axis[1]
                dz = self.nodez[i] - self.axis[2]
                d = math.sqrt((dx ** 2) + (dy ** 2) + (dz ** 2))
                self.nodex[i] += dx / d / amount
                self.nodey[i] += dy / d / amount
                self.nodez[i] += dz / d / amount

        def changecube(cubenumber):
            #If sizing is incorrect on actual tree vs on virtual tree, can adjust
            #these values until proportioned the same as on virtual tree.
            cubesize = 0.425
            cubeheight = 1

            #Data for each cube

            #axis: centre point of cube
            #nodes: coordinates of each node of cube
            #vectors: index of each node connected to another node
            #vectorcolours: colour of each vector, in parallel with vector list
            #nodecolour: colour of all nodes
            match cubenumber:
                case 1:
                    return Object([0, 0, cubeheight], [[cubesize, -cubesize, cubeheight + cubesize], [cubesize, cubesize, cubeheight + cubesize], [-cubesize, cubesize, cubeheight + cubesize], [-cubesize, -cubesize, cubeheight + cubesize],
                                       [cubesize, -cubesize, cubeheight - cubesize], [cubesize, cubesize, cubeheight - cubesize], [-cubesize, cubesize, cubeheight - cubesize], [-cubesize, -cubesize, cubeheight - cubesize]],
                              
                                      [[0, 1], [1, 2], [2, 3], [3, 0],
                                       [4, 5], [5, 6], [6, 7], [7, 4],
                                       [0, 4], [1, 5], [3, 7], [2, 6]],
                                       
                                       [Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255),
                                        Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255),
                                        Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255)],
                                        
                                        Color(255, 0, 255))
                case 2:
                    return Object([0, 0, cubeheight], [[cubesize, -cubesize, cubeheight + cubesize], [cubesize, cubesize, cubeheight + cubesize], [-cubesize, cubesize, cubeheight + cubesize], [-cubesize, -cubesize, cubeheight + cubesize],
                                       [cubesize, -cubesize, cubeheight - cubesize], [cubesize, cubesize, cubeheight - cubesize], [-cubesize, cubesize, cubeheight - cubesize], [-cubesize, -cubesize, cubeheight - cubesize]],
                              
                                      [[0, 1], [1, 2], [2, 3], [3, 0],
                                       [4, 5], [5, 6], [6, 7], [7, 4],
                                       [0, 4], [1, 5], [3, 7], [2, 6],
                               
                                       [0, 2], [1, 3]],
                                       
                                       [Color(0, 255, 0), Color(255, 255, 0), Color(0, 255, 0), Color(255, 255, 0),
                                        Color(0, 255, 0), Color(255, 255, 0), Color(0, 255, 0), Color(255, 255, 0),
                                        Color(0, 0, 255), Color(0, 0, 255), Color(0, 0, 255), Color(0, 0, 255),
                   
                                        Color(255, 255, 255), Color(255, 255, 255)],
                                        
                                        Color(255, 0, 0))
                case 3:
                    return Object([0, 0, cubeheight], [[cubesize, -cubesize, cubeheight + cubesize], [cubesize, cubesize, cubeheight + cubesize], [-cubesize, cubesize, cubeheight + cubesize], [-cubesize, -cubesize, cubeheight + cubesize],
                                       [cubesize, -cubesize, cubeheight - cubesize], [cubesize, cubesize, cubeheight - cubesize], [-cubesize, cubesize, cubeheight - cubesize], [-cubesize, -cubesize, cubeheight - cubesize]],
                              
                                      [[0, 1], [1, 2], [2, 3], [3, 0],
                                       [4, 5], [5, 6], [6, 7], [7, 4],
                                       [0, 4], [1, 5], [3, 7], [2, 6],
                               
                                       [0, 2], [1, 3],
                                       [4, 6], [5, 7],
                                       [4, 3], [0, 7],
                                       [5, 2], [6, 1],
                                       [0, 5], [4, 1],
                                       [2, 7], [3, 6]],
                                       
                                       [Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255),
                                        Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255),
                                        Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255), Color(255, 255, 255),
                   
                                        Color(0, 0, 255), Color(0, 0, 255),
                                        Color(0, 0, 255), Color(0, 0, 255),
                                        Color(255, 0, 0), Color(255, 0, 0),
                                        Color(255, 0, 0), Color(255, 0, 0),
                                        Color(0, 255, 0), Color(0, 255, 0),
                                        Color(0, 255, 0), Color(0, 255, 0),],
                                        
                                        Color(255, 255, 0))

#Adds a number of spheres in steps between each pair of vector connecting nodes
def drawVector(p1x, p1y, p1z, p2x, p2y, p2z, radius, density, colour):
    dx = p1x - p2x
    dy = p1y - p2y
    dz = p1z - p2z
    d = math.sqrt((dx ** 2) + (dy ** 2) + (dz ** 2))
    i = d / density
    drawnum = 0
    while(drawnum < d):
        xstep = drawnum * dx / d
        ystep = drawnum * dy / d
        zstep = drawnum * dz / d
        ps.add_particle(Sphere(p2x + xstep, p2y + ystep, p2z + zstep, radius, colour))
        drawnum += i

def run():
    global ps

    #If running too slow, lower this value to reduce the amount of spheres per vector.
    #The timing should be that it changes into the second cube just after 1 minute.
    #Still looks good at 5 spheres per vector but if it can be set between 5 and 10 to
    #where the timing is correct. (Unless it absolutely chugs on the raspberry pi, then
    #you can put it at 3 or 4 haha)
    spherespervector = 4
    
    #Morse code: stones are a lot like people except they think more and say less
    msg = "1010100011100011101110111000111010001000101010000000101110001011101000100000001011100000001011101010001110111011100011100000001011101010001010001110101110001000000010111011101000100011101110111000101110111010001011101010001000000010001110101011100011101011101000100010111011101000111000000011100010101010001000111010111011100000001110001010101000101000111010001110101110000000111011100011101110111000101110100010000000101110001110100011101010000000101010001011100011101011101110000000101110101000100010101000101010"
    msgnum = 0

    stonepos = 5

    phasetimer = 0
    phasenum = 0

    rottimer = random.randint(25, 100)
    targetrotx = random.uniform(-0.05, 0.05)
    targetroty = random.uniform(-0.05, 0.05)
    velrotx = 0
    velroty = 0

    roygbiv = [Color(255, 0, 0),
               Color(255, 127, 0),
               Color(255, 255, 0),
               Color(0, 255, 0),
               Color(0, 0, 255),
               Color(148, 0, 211)]
    rainbowindex = 0

    #Radius of cube spheres
    radius = RangeAttr("Thickness", 0.1, 0.05, 0.15, 0.01)

    #Set current cube and change size larger than tree for start of shrinking transition
    cube = Object.changecube(1)
    cube.changesize(1)

    while True:
        tree.black()
        ps = ParticleSystem(tree) #Refresh particlesystem (clear screen)

        #Set new random value for target rotation after timer
        rottimer -= 1
        if rottimer == 0:
            rottimer = random.randint(25, 100)
            targetrotx = random.uniform(-0.05, 0.05)
            targetroty = random.uniform(-0.05, 0.05)

        #Add to rotation values rotx, roty, with velocity working towards target rotation value
        if cube.rotx < targetrotx:
            velrotx += 0.0005
            if velrotx > 0.01:
                velrotx = 0.01
        else:
            velrotx -= 0.0005
            if velrotx < -0.01:
                 velrotx = -0.01
        if cube.roty < targetroty:
            velroty += 0.0005
            if velroty > 0.01:
                velroty = 0.01
        else:
            velroty -= 0.0005
            if velroty < -0.01:
                velroty = -0.01
        cube.rotx += velrotx
        cube.roty += velroty

        #Rotate cube nodes around axis by amount rotx, roty
        for i in range(len(cube.nodex)):
            #Rotate left/right (x,y)
            x = cube.nodex[i] - cube.axis[0]
            y = cube.nodey[i] - cube.axis[1]
            d = math.hypot(y, x)
            theta = math.atan2(y, x) + cube.rotx
            cube.nodex[i] = cube.axis[0] + d * math.cos(theta)
            cube.nodey[i] = cube.axis[1] + d * math.sin(theta)
            #Rotate up/down (x,z)
            x = cube.nodex[i] - cube.axis[0]
            z = cube.nodez[i] - cube.axis[2]
            d = math.hypot(z, x)
            theta = math.atan2(z, x) + cube.roty
            cube.nodex[i] = cube.axis[0] + d * math.cos(theta)
            cube.nodez[i] = cube.axis[2] + d * math.sin(theta)

        #Current scene/transition
        match phasenum:
            case 0: #Shrink down until viewable size
                cube.changesize(-20)
                phasetimer += 1
                if phasetimer == 20:
                    phasetimer = 0
                    phasenum += 1
            case 1: #"Stone" lower down until reaches top of tree
                ps.add_particle(Sphere(cube.axis[0], cube.axis[1], stonepos, 0.18, Color(255, 255, 255)))
                stonepos -= 0.01
                if stonepos <= 2.5:
                    phasenum += 1
            case 2: #Cube fires vector lasers from nodes at stone in secret morse code pattern
                msgnum += 0.5
                if msg[int(msgnum)] == str(1):
                    ps.add_particle(Sphere(cube.axis[0], cube.axis[1], 2.5, 0.18, Color(255, 255, 255)))
                    for i in range(len(cube.nodex)):
                        if cube.nodez[i] > cube.axis[2]:
                            ps.add_particle(Sphere(cube.nodex[i], cube.nodey[i], cube.nodez[i], radius.get() + 0.06, Color(255, 0, 0)))
                            drawVector(cube.nodex[i], cube.nodey[i], cube.nodez[i], 0, 0, 2.5, 0.09, 6, roygbiv[rainbowindex])
                            rainbowindex += 1
                            if rainbowindex == len(roygbiv):
                                rainbowindex = 0
                elif int(msgnum) == len(msg) - 1:
                    msgnum = 0
                    phasenum += 1
            case 3: #Stone is powered up and lowers down until touching cube
                ps.add_particle(Sphere(cube.axis[0], cube.axis[1], stonepos, 0.18, roygbiv[rainbowindex]))
                rainbowindex += 1
                if rainbowindex == len(roygbiv):
                    rainbowindex = 0
                stonepos -= 0.01
                if stonepos <= cube.axis[2] + 0.5:
                    stonepos = 5
                    phasenum += 1
            case 4: #Cube shrinks down
                cube.changesize(-19)
                phasetimer += 1
                if phasetimer == 10:
                    cube = Object.changecube(2)
                    cube.changesize(-1)
                    phasetimer = 0
                    phasenum += 1
            case 5: #Transforms into RGB cube with single white face and grows in size
                cube.changesize(19)
                phasetimer += 1
                if phasetimer == 10:
                    phasetimer = 0
                    phasenum += 1
            case 6: #Grow in size after timer until larger than tree, then transform into final full faced cube shrunken down
                phasetimer += 1
                if phasetimer > 800:
                    cube.changesize(100)
                    if phasetimer > 925:
                        cube = Object.changecube(3)
                        cube.changesize(-1)
                        phasetimer = 0
                        phasenum += 1
            case 7: #Grow in size until visible
                cube.changesize(19)
                phasetimer += 1
                if phasetimer == 10:
                    phasetimer = 0
                    phasenum += 1
            case 8: #After timer, shrink down and change into first cube again, loop back to the first phase
                phasetimer += 1
                if phasetimer > 800:
                    cube.changesize(-19)
                    if phasetimer == 820:
                        cube = Object.changecube(1)
                        cube.changesize(1)
                        phasetimer = 0
                        phasenum = 0

        #Draw nodes
        for i in range(len(cube.nodex)):
            ps.add_particle(Sphere(cube.nodex[i], cube.nodey[i], cube.nodez[i], radius.get() + 0.06, cube.nodecolour))

        #Draw vectors connecting nodes
        for n in range(len(cube.vector1)):
            drawVector(cube.nodex[cube.vector1[n]], cube.nodey[cube.vector1[n]], cube.nodez[cube.vector1[n]],
                       cube.nodex[cube.vector2[n]], cube.nodey[cube.vector2[n]], cube.nodez[cube.vector2[n]],
                       radius.get(),
                       spherespervector,
                       cube.vectorcolours[n])

        ps.fast_draw()
        tree.update()
