import time
import math
from gridmas import *

fps = 15
totalFrames = 70
pokeballShellRadius = 0.5
pokeballOutlineRadius = 0.2
pokeballButtonRadius = 0.3

currentFrame = 0
pokeballThrowFrames = 30
pikachuFlashFrames = 32
pikachuSparkFrames = 40 

pikachuRevealFrame = pikachuFlashFrames + 1
pikachuSparkEnd = pikachuRevealFrame + pikachuSparkFrames


def draw():
    global currentFrame

    if currentFrame <= pokeballThrowFrames:
        pokeballThrow()

    elif currentFrame <= pikachuFlashFrames:
        pikachuFlash()

    elif currentFrame <= pikachuSparkEnd:
        pikachu(spark=True)

    else:
        pikachu(spark=False)

    currentFrame += 1


def pokeballThrow():
    frame = currentFrame
    t = frame / (pokeballThrowFrames - 1)

    # clears the tree
    for pixel in pixels():
        pixel.set(Color(0, 0, 0))

    # throw path of the ball. THe bottom left to the center
    startPos = (-1, -1, 0)
    endPos = (0, 0, 2)

    ballX = startPos[0] + t * (endPos[0] - startPos[0])
    ballY = startPos[1] + t * (endPos[1] - startPos[1])
    ballZ = startPos[2] + t * (endPos[2] - startPos[2])

    # draw pokeball
    for pixel in pixels():
        dist = math.sqrt(
            (pixel.x - ballX)**2 +
            (pixel.y - ballY)**2 +
            (pixel.z - ballZ)**2
        )

        if dist < pokeballButtonRadius:
            pixel.set(Color(200, 200, 200))
        elif pokeballButtonRadius < dist < pokeballShellRadius:
            if pixel.z < ballZ:
                pixel.set_rgb(255, 255, 255)
            else:
                pixel.set(Color(255, 0, 0))
        elif pokeballButtonRadius < dist < pokeballShellRadius < pokeballOutlineRadius:
            pixel.set(Color(0, 0, 0))


def pikachuFlash():
    if pokeballThrowFrames < currentFrame <= pikachuFlashFrames:
        for pixel in pixels():
            pixel.set(Color(255, 255, 255))
        return


def pikachu(spark=False):

   
    if spark:
        headColor = Color(255, 255, 255) if currentFrame % 2 == 0 else Color(255, 220, 0)
    else:
        headColor = Color(255, 220, 0)

    for pixel in pixels():
        pixel.set(Color(0, 0, 0))

  
    centerX, centerY, centerZ = 0, 0, 1

   
    headRadius = pokeballShellRadius * 1.0
    earHeight = pokeballShellRadius * 2.2
    earBaseWidth = pokeballShellRadius * 1.2
    earTipWidth = pokeballShellRadius * 0.5
    earOffsetY = headRadius * 1.4
    earBaseZ = centerZ + headRadius * 0.5

    for pixel in pixels():
       
        if abs(pixel.x - centerX) > pokeballShellRadius * 1.2:
            continue

        headDist = math.sqrt((pixel.y - centerY)**2 + (pixel.z - centerZ)**2)
        if headDist < headRadius:
            pixel.set(headColor)
            continue

 
        gapWidth = pokeballShellRadius * 0.6
        gapZMin = centerZ + headRadius * 1.1
        gapZMax = gapZMin + earHeight * 0.85
        if abs(pixel.y - centerY) < gapWidth and gapZMin < pixel.z < gapZMax:
            pixel.set(Color(0, 0, 0))
            continue

        def ear(yCenter):
            dz = pixel.z - earBaseZ
            if 0 <= dz <= earHeight:
                taper = 1 - (dz / earHeight)
                width = earTipWidth + taper * (earBaseWidth - earTipWidth)
                return abs(pixel.y - yCenter) < width
            return False

 
        if ear(centerY - earOffsetY):
            pixel.set(headColor)
            continue

      
        if ear(centerY + earOffsetY):
            pixel.set(headColor)
