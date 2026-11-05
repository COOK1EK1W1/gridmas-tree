'''
Every visual in this show is created procedurally using my custom framework.
It allows 6 degrees of freedom, custom shapes, patterns, custom union functions, all fully dynamic.
No external modules were used, other than gridmas.
'''

import time
import math
from gridmas import *

from types import MethodType
from abc import ABC, abstractmethod

class Shape(ABC):
    def __init__(self, position, rotation):
        self.position = position
        self.rotation = rotation

    
    def get_pixel_position(self, pixel):
        # Unpack variables
        pixel_x, pixel_y, pixel_z = pixel
        x_pos, y_pos, z_pos = self.position

        # Translate the pixels to shape origin
        pixel_x -= x_pos
        pixel_y -= y_pos
        pixel_z -= z_pos

        # Rotate pixels around shape
        rotated_point = rotate((pixel_x, pixel_y, pixel_z), self.sin_rotation, self.cos_rotation)

        return rotated_point

    @abstractmethod
    def get_distance(self, position: tuple[float, float, float]) -> float:
        ...

    @abstractmethod
    def get_pattern_value(self, position: tuple[float, float, float]) -> Color:
        ...

    @abstractmethod
    def get_color(self, pixel: tuple[float, float, float]) -> Optional[Color]:
        ...

    def update_cached_variables(self):
        self.sin_rotation = (
            math.sin(math.radians(self.rotation[0])),
            math.sin(math.radians(self.rotation[1])),
            math.sin(math.radians(self.rotation[2])),
        )
        self.cos_rotation = (
            math.cos(math.radians(self.rotation[0])),
            math.cos(math.radians(self.rotation[1])),
            math.cos(math.radians(self.rotation[2])),
        )


class Primitive(Shape):
    def __init__(self, position, starting_rotation, shape_args, pattern_args):
        super().__init__(position, starting_rotation)

        self.distance_function = shape_args[0]
        self.shape_args = shape_args[1:]

        self.pattern_function = pattern_args[0]
        self.pattern_args = pattern_args[1:]
    

    def get_distance(self, position):
        # Get distance
        distance = self.distance_function(self.shape_args, position)

        return distance

    def get_pattern_value(self, position):
        # Get color
        pixel_color = self.pattern_function(self.pattern_args, position)

        return pixel_color

    # Wrapper function. might change
    def get_color(self, pixel: tuple[float, float, float]) -> Optional[Color]:
        world_space_pixel = super().get_pixel_position(pixel)

        if (self.get_distance(world_space_pixel) > 0):
            return None

        return self.get_pattern_value(world_space_pixel)


class CompositeShape(Shape):
    def __init__(self, position, starting_rotation, shape_a, shape_b, shape_args, pattern_args):

        super().__init__(position, starting_rotation)

        # Shape objects
        self.shape_a = shape_a
        self.shape_b = shape_b  

        self.shapeUnion = shape_args[0]  # union function. i.e. additive: min(a, b)
        self.shape_args = shape_args[1:]

        self.patternUnion = pattern_args[0]
        self.pattern_args = pattern_args[1:]

    def get_distance(self, position):
        position_a = self.shape_a.get_pixel_position(position)
        position_b = self.shape_b.get_pixel_position(position)        

        a_distance = self.shape_a.get_distance(position_a)
        b_distance = self.shape_b.get_distance(position_b)

        distance = self.shapeUnion(self.shape_args, a_distance, b_distance)
        return distance

    def get_pattern_value(self, position):
        # Rotate and translate for element shapes
        position_a = self.shape_a.get_pixel_position(position)
        position_b = self.shape_b.get_pixel_position(position)        

        a_distance = self.shape_a.get_distance(position_a)
        b_distance = self.shape_b.get_distance(position_b)

        distance = self.shapeUnion(self.shape_args, a_distance, b_distance)

        a_color = self.shape_a.get_pattern_value(position_a)
        b_color = self.shape_b.get_pattern_value(position_b)
        color = self.patternUnion(self.pattern_args, a_distance, a_color, b_distance, b_color)

        return color

    def get_color(self, pixel: tuple[float, float, float]) -> Optional[Color]:
        world_space_pixel = super().get_pixel_position(pixel)

        if (self.get_distance(world_space_pixel) > 0):
            return None

        return self.get_pattern_value(world_space_pixel)

            

    def move_centre(self, value):
        x, y, z = value

        self.position[0] += x
        self.position[1] += y
        self.position[2] += z

        self.shape_a.position[0] -= x
        self.shape_a.position[1] -= y
        self.shape_a.position[2] -= z
        
        self.shape_b.position[0] -= x
        self.shape_b.position[1] -= y
        self.shape_b.position[2] -= z

    def update_cached_variables(self):
        super().update_cached_variables()

        self.shape_a.update_cached_variables()
        self.shape_b.update_cached_variables()


class Sphere(Primitive):
    def __init__(self, pos: tuple[float, float, float], radius: float, color: Color):
        super().__init__(pos, [0, 0, 0], [sdSphere, radius], [patternSolid, color])


class Box(Primitive):
    def __init__(self, pos: tuple[float, float, float], size: tuple[float, float, float], color: Color):
        super().__init__(pos, [0, 0, 0], [sdBox, size[0], size[1], size[2]], [patternSolid, color])


class Cylinder(Primitive):
    def __init__(self, pos: tuple[float, float, float], radius, height, color: Color):
        super().__init__(pos, [0, 0, 0], [sdCylinder, radius, height], [patternSolid, color])


class Plane(Primitive):
    def __init__(self, pos: tuple[float, float, float], color: Color):
        super().__init__(pos, [0, 0, 0], [sdPlane], [patternSolid, color])


def rotate(point, sin_rotation, cos_rotation):
    sin_x, sin_y, sin_z = sin_rotation
    cos_x, cos_y, cos_z = cos_rotation


    x, y, z = point

    # Around X - Pitch
    y, z = (y*cos_x - z*sin_x), (y*sin_x + z*cos_x)

    # Rotate around Y (yaw)
    x, z = x * cos_y + z * sin_y, -x * sin_y + z * cos_y

    # Rotate around Z (roll)
    x, y = x * cos_z - y * sin_z, x * sin_z + y * cos_z

    return (x, y, z)



# Signed Distance Functions
# How far is point from the closest surface of shape

def sdPlane(shape_args, point):
    x, y, z = point

    return z 

def sdSphere(shape_args, point):

    x, y, z = point

    return math.hypot(x, y, z) - shape_args[0]

def sdBox(shape_args, point):

    depth, width, height = shape_args
    x, y, z = point

    qx = abs(x) - depth
    qy = abs(y) - width
    qz = abs(z) - height

    a = math.hypot(max(qx, 0.0), max(qy, 0.0), max(qz, 0.0))
    b = min(max(qx, max(qy, qz)), 0.0)

    return a+b

def sdBoxFrame(shape_args, point):

    depth, width, height, thickness = shape_args
    x, y, z = point

    px = abs(x) - depth
    py = abs(y) - width
    pz = abs(z) - height

    qx = abs(px+thickness) - thickness
    qy = abs(py+thickness) - thickness
    qz = abs(pz+thickness) - thickness

    a = math.hypot(max(px, 0.0), max(qy, 0.0), max(qz, 0.0)) + min(max(px, max(qy, qz)), 0.0)
    b = math.hypot(max(qx, 0.0), max(py, 0.0), max(qz, 0.0)) + min(max(qx, max(py, qz)), 0.0)
    c = math.hypot(max(qx, 0.0), max(qy, 0.0), max(pz, 0.0)) + min(max(qx, max(qy, pz)), 0.0)

    return min(a, min(b, c))

def sdCone(shape_args, point):

    cone1, cone2, height = shape_args
    x, y, z = point

    q = math.hypot(x, z)
    return max(cone1 * q + cone2 * y, -height - y)

def sdCylinder(shape_args, point):
    radius, height = shape_args
    x, y, z = point

    dx = math.hypot(x, z) - radius
    dy = abs(y) - height

    max_d = max(dx, dy)
    term1 = min(max_d, 0.0)

    dx = max(dx, 0.0)
    dy = max(dy, 0.0)
    term2 = math.hypot(dx, dy)

    return term1 + term2


# Example for an operation that can be used on 2d SDFs
def sd2dRevolution(self, point):

    primitive, primitive_args, axis_distance = self.shape_args

    x, y, z = point

    q = math.hypot(x, z) - axis_distance, y

    primitive_distance = primitive(primitive_args, q)

    return primitive_distance

def sd2dCircle(self, point):

    x, y = point
    return math.hypot(x, y) - shape_args


# Pattern functions
def patternSolid(pattern_args, point):

    return pattern_args[0]

def patternSplit(pattern_args, point):
        
    a, b = pattern_args
    x, y, z = point

    if (z >= 0):
        return a
    else:
        return b
    
def patternAxis(pattern_args, point):

    x, y, z = point
    return Color(int(x*10), int(y*10), int(z*10))

def patternRainbow(pattern_args, point):

    x, y, z = point
    return Color(int(x*255), int(y*255), int(z*255))

def patternPastel(pattern_args, point):
    x, y, z = point
    x, y, z = (x+1)/2, (y+1)/2, (z+1)/2
    return Color(int(x*255), int(y*255), int(z*255))

def patternPresent(pattern_args, point):

    x, y, z = point
    box_col, stripe_col, stripe_thickness = pattern_args

    if (x >= -(stripe_thickness/2)) and (x <= (stripe_thickness/2)):
        return stripe_col
    if (y >= -(stripe_thickness/2)) and (y <= (stripe_thickness/2)):
        return stripe_col
    
    return box_col

def patternGradient(pattern_args, point):
    x, y, z = point 
    top_col, bottom_col, pattern_height = pattern_args

    t = max(0, min(1, (y + pattern_height)))

    r = int(top_col.r * (1 - t) + bottom_col.r * t)
    g = int(top_col.g * (1 - t) + bottom_col.g * t)
    b = int(top_col.b * (1 - t) + bottom_col.b * t)

    return Color(r, g, b)


# Operations - shape or pattern
def opTwistX(func_args, point):
    k, func, interior_args = func_args

    x, y, z = point

    c = math.cos(k * x)
    s = math.sin(k * x)

    # 2x2 rotation applied to (x, z)
    qy = c * y - s * z
    qz = s * y + c * z

    return func(interior_args, (x, qy, qz))

def opTwistY(func_args, point):
    k, func, interior_args = func_args

    x, y, z = point

    c = math.cos(k * y)
    s = math.sin(k * y)

    # 2x2 rotation applied to (x, z)
    qx = c * x - s * z
    qz = s * x + c * z

    return func(interior_args, (qx, y, qz))

def opTwistZ(func_args, point):
    k, func, interior_args = func_args

    x, y, z = point

    c = math.cos(k * z)
    s = math.sin(k * z)

    # 2x2 rotation applied to (x, z)
    qx = c * x - s * y
    qy = s * x + c * y

    return func(interior_args, (qx, qy, z))

def opTile(func_args, point):
    k, func, interior_args = func_args

    x, y, z = point

    qx = x % k
    qy = y % k
    qz = z % k


    return func(interior_args, (qx, qy, qz))

# Union functions - shape
def sdUnionAddition(shape_args, a, b):

    return min(a, b)

def sdUnionIntersection(shape_args, a, b):

    return max(a, b)

def sdUnionSubtraction(shape_args, a, b):

    return max(a, -b)

def sdUnionSmooth(shape_args, a, b):
    k = shape_args[0]

    if (k == 0):
        return sdUnionAddition(None,a, b)

    h = min(max(0.5 + 0.5*(a - b)/k, 0.0), 1.0)
    dist = ((a*(1-h))+(b*h)) - k*h*(1.0-h)

    return dist

def sdUnionLerp(shape_args, a, b):
    k = shape_args[0]
    return (a * (1 - k)) + (b * k)


# Union functions - pattern
def patternUnionClosest(pattern_args, dist_a, col_a, dist_b, col_b):
    if (dist_a <= dist_b):
        return col_a
    else:
        return col_b 

def patternUnionSmooth(pattern_args, dist_a, col_a, dist_b, col_b):

    k = pattern_args[0]

    if (k == 0):
        return patternUnionClosest(None, dist_a, col_a, dist_b, col_b)

    h = min(max(0.5 + 0.5*(dist_a - dist_b)/k, 0.0), 1.0)


    r = ((col_a.r*(1-h))+(col_b.r*h)) - k*h*(1.0-h)
    g = ((col_a.g*(1-h))+(col_b.g*h)) - k*h*(1.0-h)
    b = ((col_a.b*(1-h))+(col_b.b*h)) - k*h*(1.0-h)

    return Color(int(r), int(g), int(b))

def patternUnionLerp(pattern_args, dist_a, col_a, dist_b, col_b):
    k = pattern_args[0]

    r = (col_a.r * (1 - k)) + (col_b.r * k)
    g = (col_a.g * (1 - k)) + (col_b.g * k)
    b = (col_a.b * (1 - k)) + (col_b.b * k)


    return Color(int(r), int(g), int(b))


background_color = Color(0, 0, 0)

objects = []

start_time = time.time()
current_time = start_time

act_times = [
    5,   # Cube grows
    10,  # Star descends
    10,  # Cube becomes box
    5,   # Box spins, shrinks and descends
    10,  # Tree grows
    6,  # Spheres move through tree
    5,  # Tree becomes cube
    5,  # Cube becomes pillar
    10,  # Pillar twists
    10,  # Pillar turns into tree
    5,  # Box expands
    5,  # Fade out
    1,  # End/Loop
]
current_act = 0
previous_act = -1

def draw():
    global previous_act, current_act, current_time, objects, start_time, previous_time


    # This timer will determine what act occurs
    previous_time = current_time
    current_time = time.time() - start_time 
    delta_time = current_time - previous_time

    # Fix for the first frame
    if (delta_time < 0):
        delta_time = 0.2

    # Timing (seconds)
    for i in range(len(act_times)):
        if (current_time <= sum(act_times[:i+1])):
            current_act = i+1
            break

    # Did the act just change
    new_act = (previous_act != current_act)
    previous_act = current_act


    # Acts
    match current_act:
        # Cube grows and rises
        case 1:  
            if new_act:
                # Spawn 0 size cube at (0, 0, 0)
                cube = Primitive([0, 0, 0], [0, 0, 0], 
                                [sdBox, 0, 0, 0],
                                [patternPastel])
                                
                objects.append(cube)

            # Grow to 0.45
            objects[0].shape_args[0] += 0.09*delta_time
            objects[0].shape_args[1] += 0.09*delta_time
            objects[0].shape_args[2] += 0.09*delta_time

            # Move up
            objects[0].position[2] += 0.2*delta_time

            # Spin around z
            objects[0].rotation[2] += 36*delta_time

        # Star descends into cube
        case 2:
            if new_act:
                star = Sphere([0, 0, 6], 0.3, Color(255, 215, 0))

                objects = [CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    objects[0], star,
                    [sdUnionSmooth, 0.9],
                    [patternUnionSmooth, 0.9],

                )]

            objects[0].shape_a.rotation[2] += 36*delta_time
            objects[0].shape_b.position[2] -= 0.5*delta_time


        # Cube/star morphs into spinning frame box
        case 3:
            if new_act:
                frame_box = Primitive(
                    [0, 0, 1], objects[0].shape_a.rotation,
                    [sdBoxFrame, 0.45, 0.45, 0.45, 0.1],
                    [patternSolid, Color(0,110,51)]
                )

                objects = [CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    objects[0], frame_box,
                    [sdUnionLerp, 0.0],
                    [patternUnionLerp, 0.0]
                )]
                objects[0].move_centre((0, 0, 1))

            objects[0].rotation[0] += 36*delta_time
            objects[0].rotation[1] += 36*delta_time
            objects[0].rotation[2] += 36*delta_time

            # Lerp from cube/star to box frame
            objects[0].shape_args[0] += 0.1 * delta_time
            objects[0].pattern_args[0] += 0.1 * delta_time

        # Box spins, shrinks and descends
        case 4:
            if new_act:
                objects = [objects[0].shape_b]
                objects[0].position = [0, 0, 1]

            objects[0].shape_args[0] -= 0.09*delta_time
            objects[0].shape_args[1] -= 0.09*delta_time
            objects[0].shape_args[2] -= 0.09*delta_time

            objects[0].position[2] -= 0.25*delta_time
            
            objects[0].rotation[0] += 36*delta_time
            objects[0].rotation[1] += 36*delta_time
            objects[0].rotation[2] += 36*delta_time
        
        # Tree grows
        case 5:
            if new_act:
                
                trunk = Primitive(
                    [0, 0, -2], [90, 0, 0],
                    [sdCylinder, 0.2, 0.3],
                    [patternSolid, Color(165, 42, 42)]
                )
                
                leaves = Primitive(
                    [0, 0, 0.25], [-90, 0, 0],
                    [sdCone, 0.5, 0.2, 2.0],
                    #[patternGradient, Color(0, 150, 37), Color(7,86,0), 1.0]
                    [patternGradient, Color(0, 255, 0), Color(255,0,0), 1.0]
                )


                objects = [trunk, leaves]

            objects[0].position[2] += 0.25*delta_time
            objects[1].position[2] += 0.25*delta_time

        # Spheres move through tree
        case 6:
            if new_act:
                star = Sphere([0, 2, 1.5], 0.2, Color(255, 15, 255))

                objects[1] = CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    objects[1], star,
                    [sdUnionSmooth, 0.5], 
                    [patternUnionSmooth, 0.5]
                )

                global flag
                flag = False

            if objects[1].shape_b.position[1] < -1:
                flag = True
                objects[1].shape_b.position[1] = 0
                objects[1].shape_b.position[0] = 2

            if flag:
                objects[1].shape_b.position[0] -= 1*delta_time
            else:
                objects[1].shape_b.position[1] -= 1*delta_time
        
        # Tree becomes cube
        case 7:
            if new_act:

                box = Primitive(
                    [0, 0, 1.25], [0, 0, 0],
                    [sdBox, 0.45, 0.45, 0.45],
                    [patternRainbow]
                )

                tree = CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    objects[0], objects[1].shape_a,
                    [sdUnionAddition],
                    [patternUnionClosest]
                )


                objects = [CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    tree, box,
                    [sdUnionLerp, 0.0],
                    [patternUnionLerp, 0.0]
                )]
            
            objects[0].shape_args[0] += 0.2 * delta_time
            objects[0].pattern_args[0] += 0.2 * delta_time

        case 8:
            if new_act:
                box = Primitive(
                    [0, 0, 1.25], [0, 0, 0],
                    [sdBox, 0.45, 0.45, 0.45],
                    [patternRainbow]
                )

                pillar = Primitive(
                    [0, 0, 2.5], [90, 90, 0],
                    [sdBox, 0.45, 6, 0.45],
                    [patternSplit, Color(255, 0, 0), Color(0, 255, 0)]
                )

                objects = [CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    box, pillar,
                    [sdUnionLerp, 0.0],
                    [patternUnionLerp, 0.0]
                )]

            objects[0].shape_args[0] += 0.2 * delta_time
            objects[0].pattern_args[0] += 0.2 * delta_time
        
        case 9:
            if new_act:
                objects = [Primitive(
                        [0, 0, 2.5], [90, 90, 0],
                        [opTwistY, 0.0, sdBox, (0.45, 6, 0.45)],
                        [opTwistY, 0.0, patternSplit, (Color(255, 0, 0), Color(0, 255, 0))]
                    )
                ]

            objects[0].shape_args[0] += 0.25 * delta_time
            objects[0].pattern_args[0] += 0.25 * delta_time  

        case 10:
            if new_act:
                trunk = Primitive(
                    [0, 0, 0.5], [90, 0, 0],
                    [sdCylinder, 0.2, 0.3],
                    [patternSolid, Color(165, 42, 42)]
                )
                
                leaves = Primitive(
                    [0, 0, 2.75], [-90, 0, 0],
                    [sdCone, 0.5, 0.2, 2.0],
                    #[patternGradient, Color(0, 150, 37), Color(7,86,0), 1.0]
                    [patternGradient, Color(0, 255, 0), Color(255,0,0), 1.0]
                )

                tree = CompositeShape(
                    [0, 0, 0], [0, 0, 0],
                    trunk, leaves,
                    [sdUnionAddition],
                    [patternUnionClosest]
                )

                objects = [
                    CompositeShape(
                        [0, 0, 0], [0, 0, 0],
                        objects[0], tree,
                        [sdUnionLerp, 0.0],
                        [patternUnionLerp, 0.0]
                    )
                ]

            objects[0].shape_a.shape_args[0] += 0.24 * delta_time
            objects[0].shape_a.pattern_args[0] += 0.24 * delta_time  

            objects[0].shape_args[0] += 0.1 * delta_time
            objects[0].pattern_args[0] += 0.1 * delta_time
        
        case 11:
            if new_act:
                box = Box((0, 0, 1.25), (0, 0, 0), Color.green())

                objects = [box, objects[0].shape_b]

            objects[0].rotation[2] += 18 * delta_time

            objects[0].shape_args[0] += 0.5 * delta_time
            objects[0].shape_args[1] += 0.5 * delta_time
            objects[0].shape_args[2] += 0.5 * delta_time

        case 12:
            if new_act:
                green = Plane((0, 0, 10), Color.green())
                black = Plane((0, 0, 10), Color.black())
                objects = [
                    CompositeShape(
                        (0, 0, 0), (0, 0, 0),
                        black, green,
                        [sdUnionLerp, 1.0],
                        [patternUnionLerp, 1.0]
                    )
                ]
            objects[0].shape_args[0] -= 0.24 * delta_time
            objects[0].pattern_args[0] -= 0.24 * delta_time  


        case 13:
            if new_act:
                objects = []
                start_time = time.time()
                current_time = 0
                previous_act = 0
                current_act = 1
                return



    # Render Loop
    background(background_color)
    for pixel in pixels():

        for obj in objects:
            obj.update_cached_variables()
            pixel_value = obj.get_color((pixel.x, pixel.y, pixel.z))
            if (pixel_value != None):
                pixel.set(pixel_value)
                break