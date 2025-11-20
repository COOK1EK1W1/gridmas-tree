"""
A robust rendering engine to create custom 3d shapes in your patterns.
"""


import math
from abc import ABC, abstractmethod
from typing import Optional
from colors import Color, Pixel
from tree import tree


class Shape:
    """
    A base class with a position and a rotation
    Shared functionality for all geometry

    Args:
        ABC (abc.ABC): An abstract class
    """
    def __init__(self, position, rotation):
        """
        Create a new instance of Shape

        Args:
            position (tuple[float, float, float]): A tuple containing the x,y,z position of the shape
            rotation (tuple[float, float, float]): A tuple containing the pitch,yaw,roll rotation of the shape
        """

        self.position = position
        self.rotation = rotation

        self.is_composite = False

        self.__update_cached_variables()
        tree._shapes.append(self)

    
    def get_pixel_position(self, pixel):
        """
        Converts a tree (world) space position to shape (object) space

        Args:
            pixel (tuple[float, float, float]):A tuple containing the x,y,z position of the pixel

        Returns:
            (tuple[float, float, float]): The transformed position
        """
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
    def get_color(self, pixel: tuple[float, float, float]) -> Optional[Color]:
        ...

    def does_draw(self, pixel: Pixel) -> Optional[Color]:
        """
        Method for backwards compatibility with existing API
        Deprecated, do not use in new code

        Args:
            pixel (Pixel): The input pixel

        Returns:
            Optional[Color]: Color of pixel, if valid. Else, returns None.
        """

        return self.get_color((pixel.x, pixel.y, pixel.z))


    def __update_cached_variables(self):
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
    """
    A primitive 3d object

    Args:
        Shape: A base class with functionality for 3d geometry
    """
    def __init__(self, position, starting_rotation, shape_args, pattern_args):
        """
        Create an instance of Primitive

        Args:
            position (tuple[float, float, float]):A tuple containing the x,y,z position of the primitive
            starting_rotation (tuple[float, float, float]):A tuple containing the pitch,yaw,roll rotation of the primitive
            shape_args (tuple["sdFunction", *args]): Definition of the shape. args e.g. radius, size, thickness etc
            pattern_args (tuple["patternFunction", *args]): Definition of the pattern. args e.g. Color, stripe_thickness etc
        """

        super().__init__(position, starting_rotation)

        self.distance_function = shape_args[0]
        self.shape_args = shape_args[1:]

        self.pattern_function = pattern_args[0]
        self.color_args = pattern_args[1:]
    

    def get_distance(self, position):
        """
        Gets signed distance from a point to object surface 

        Args:
            position (tuple[float, float, float]): the object-space position of the position
        
        Returns:
            distance (float): Signed distance from point to object surface. Negative if inside.
        """
        # Get distance
        distance = self.distance_function(position)

        return distance

    def get_pattern_value(self, position):
        """
        Gets color of position using an object's pattern 

        Args:
            position (tuple[float, float, float]): the object-space position of the position

        Returns:
            pixel_color (Color): Color of pixel using object pattern
        """

        # Get color
        pixel_color = self.pattern_function(position)

        return pixel_color

    # Wrapper function. might change
    def get_color(self, pixel: tuple[float, float, float]) -> Optional[Color]:
        """
        Gets color of position if it is inside object 

        Args:
            position (tuple[float, float, float]): the object-space position of the point

        Returns:
            pixel_color (Optional[Color]): Color of pixel using object pattern if it is inside    
        """

        world_space_pixel = super().get_pixel_position(pixel)

        if (self.get_distance(world_space_pixel) <= 0):
            return self.get_pattern_value(world_space_pixel)
        else:
            return None


class CompositeShape(Shape):
    """
    A 3d object that combines two primitives,
    using custom shape and pattern intersection functions

    Args:
        Shape: A base class with functionality for 3d geometry
    """
    def __init__(self, position, starting_rotation, shape_a, shape_b, shape_args, pattern_args):
        """
        Create an instance of CompositeShape

        Args:
            position (tuple[float, float, float]):A tuple containing the x,y,z position of the composite shape
            starting_rotation (tuple[float, float, float]):A tuple containing the pitch,yaw,roll rotation of the composite shape
            shape_a (Primitive): First primitive
            shape_b (Primitive): Second primitive
            shape_args (tuple["sdUnionFunction", *args]): Definition of the shape union.
            pattern_args (tuple["patternFunction", *args]): Definition of the pattern union.
        """

        super().__init__(position, starting_rotation)

        # Shape objects
        self.shape_a = shape_a
        self.shape_b = shape_b  

        shape_a.is_composite = True
        shape_b.is_composite = True

        self.shapeUnion = shape_args[0]  # union function. i.e. additive: min(a, b)
        self.shape_args = shape_args[1:]

        self.patternUnion = pattern_args[0]
        self.pattern_args = pattern_args[1:]

        
    def get_distance(self, position):
        """
        Gets the distance of a position from the surface of the composite shape

        Args:
            position (tuple[float, float, float]): the object-space position of the point
        
        Returns:
            distance (float): the distance from the position to the surface
            
        """
        position_a = self.shape_a.get_pixel_position(position)
        position_b = self.shape_b.get_pixel_position(position)        

        a_distance = self.shape_a.get_distance(position_a)
        b_distance = self.shape_b.get_distance(position_b)

        distance = self.shapeUnion(a_distance, b_distance)
        return distance

    def get_pattern_value(self, position):
        """
        Gets the color of a position in the pattern of the composite shape

        Args:
            position (tuple[float, float, float]): the object-space position of the point
        
        Returns:
            color (Color): the color of the point in the pattern
        """

        # Rotate and translate for element shapes
        position_a = self.shape_a.get_pixel_position(position)
        position_b = self.shape_b.get_pixel_position(position)        

        a_distance = self.shape_a.get_distance(position_a)
        b_distance = self.shape_b.get_distance(position_b)

        a_color = self.shape_a.get_pattern_value(position_a)
        b_color = self.shape_b.get_pattern_value(position_b)
        color = self.patternUnion(a_distance, a_color, b_distance, b_color)

        return color

    def get_color(self, pixel: tuple[float, float, float]) -> Optional[Color]:
        """
        Gets color of pixel if it satisfies shape union function

        Args:
            pixel (tuple[float, float, float]): the world-space position of the pixel

        Returns:
            pixel_color (Optional[Color]): Color of pixel combining object patterns using pattern union function
        """

        world_space_pixel = super().get_pixel_position(pixel)

        if (self.get_distance(world_space_pixel) > 0):
            return None

        return self.get_pattern_value(world_space_pixel)



class Sphere(Primitive):
    """
    Represents a sphere of a solid color
    Used for backwards compatability and to decrease boilerplate code
    """
    def __init__(self, pos: tuple[float, float, float], radius: float, color: Color):
        super().__init__(pos, [0, 0, 0], [sdSphere, radius], [patternSolid, color])


class Box(Primitive):
    """
    Represents a box of a solid color
    Used for backwards compatability and to decrease boilerplate code
    """

    def __init__(self, pos: tuple[float, float, float], size: tuple[float, float, float], color: Color):
        super().__init__(pos, [0, 0, 0], [sdBox, size[0], size[1], size[2]], [patternSolid, color])


class Cylinder(Primitive):
    """
    Represents a cylinder of a solid color
    Used to decrease boilerplate code
    """

    def __init__(self, pos: tuple[float, float, float], radius, height, color: Color):
        super().__init__(pos, [0, 0, 0], [sdCylinder, radius, height], [patternSolid, color])


class Plane(Primitive):
    """
    Represents a plane of a solid color
    Used to decrease boilerplate code
    """

    def __init__(self, pos: tuple[float, float, float], color: Color):
        super().__init__(pos, [0, 0, 0], [sdPlane], [patternSolid, color])


def rotate(point, sin_rotation, cos_rotation):
    """
    Rotates (x, y, z) point around (0, 0, 0)

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z point to be rotated
        sin_rotation (tuple[float, float, float]): A tuple containing the sin of the pitch,yaw,roll rotation
        cos_rotation (tuple[float, float, float]): A tuple containing the cos of the pitch,yaw,roll rotation


    Returns:
        (tuple[float, float, float]): The rotated point
    """

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

def sdPlane(self, point):
    """
    Signed distance function for a flat, infinite plane
    Returns negative if point is inside

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample 

    Returns:
        (float): The signed distance to the shape surface

    Shape Args:
        None
    """

    x, y, z = point

    return z 

def sdSphere(self, point):
    """
    Signed distance function for a sphere
    Returns negative if point is inside

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample 

    Returns:
        (float): The signed distance to the shape surface

    Shape Args:
        (tuple[float]): Radius of sphere 
    """

    x, y, z = point

    return math.hypot(x, y, z) - self.shape_args[0]

def sdBox(self, point):
    """
    Signed distance function for a box
    Returns negative if point is inside

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample 

    Returns:
        (float): The signed distance to the shape surface

    Shape Args:
        (tuple[float, float, float]): The (x, y, z) dimensions of the box 
    """

    depth, width, height = self.shape_args
    x, y, z = point

    qx = abs(x) - depth
    qy = abs(y) - width
    qz = abs(z) - height

    a = math.hypot(max(qx, 0.0), max(qy, 0.0), max(qz, 0.0))
    b = min(max(qx, max(qy, qz)), 0.0)

    return a+b

def sdBoxFrame(self, point):
    """
    Signed distance function for a box frame
    Returns negative if point is inside

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample 

    Returns:
        (float): The signed distance to the shape surface

    Shape Args:
        (tuple[float, float, float, float]): The (x, y, z) dimensions of the box and the width of the frame
        
    """

    depth, width, height, thickness = self.shape_args
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

def sdCone(self, point):
    """
    Signed distance function for a finite cone
    Returns negative if point is inside

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample 

    Returns:
        (float): The signed distance to the shape surface

    Shape Args:
        (tuple[float, float, float]): Two slope variables and the height
        
    """

    cone1, cone2, height = self.shape_args
    x, y, z = point

    q = math.hypot(x, z)
    return max(cone1 * q + cone2 * y, -height - y)

def sdCylinder(self, point):
    """
    Signed distance function for a finite cylinder
    Returns negative if point is inside

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample 

    Returns:
        (float): The signed distance to the shape surface
    
    Shape Args:
        (tuple[float, float]): (radius, height) of the cylinder
    """
    radius, height = self.shape_args
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
    """
    Revolves a 2D signed distance function around the Y-axis.

    Args:
        point (tuple[float, float, float]): A tuple containing the point x,y,z to sample.

    Returns:
        float: Signed distance after revolution.
    
    Shape Args:
        (tuple[sdFunction, tuple, float]): (primitive_function, primitive_args, axis_distance)
    """

    primitive, primitive_args, axis_distance = self.shape_args

    x, y, z = point

    q = math.hypot(x, z) - axis_distance, y

    primitive_distance = primitive(primitive_args, q)

    return primitive_distance

def sd2dCircle(self, point):
    """
    Signed distance function for a 2D circle.

    Args:
        point (tuple[float, float]): A tuple containing the x, y to sample.

    Returns:
        float: Signed distance to the shape surface.

    Shape Args:
        (float): Radius of the circle.
    """

    x, y = point
    return math.hypot(x, y) - self.shape_args


# Pattern functions
def patternSolid(self, point):
    """
    Pattern function for a solid color
    Query an object space (x, y, z) point

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z position of the point to be queried

    Return:
        (Color) : Calculated color at point

    Color Args:
        (tuple[Color]): Color of shape
    
    """

    return self.color_args[0]

def patternSplit(self, point):
    """
    Pattern function for 2 vertically split colors 
    Query an object space (x, y, z) point

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z position of the point to be queried

    Return:
        (Color) : Calculated color at point

    Color Args:
        (tuple[Color, Color]): Top color, bottom color 
    
    """
        
    a, b = self.color_args
    x, y, z = point

    if (z >= 0):
        return a
    else:
        return b
    
def patternAxis(self, point):
    """
    Pattern function that returns a different color per octant
    Query an object space (x, y, z) point

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z position of the point to be queried

    Return:
        (Color) : Calculated color at point
    
    """

    x, y, z = point
    return Color(int(x*10), int(y*10), int(z*10))

def patternRainbow(self, point):
    """
    Pattern function for a rainbow pattern
    Query an object space (x, y, z) point

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z position of the point to be queried

    Return:
        (Color) : Calculated color at point
    
    """
    x, y, z = point
    return Color(int(x*255), int(y*255), int(z*255))

def patternPastel(self, point):
    """
    Pattern function for a pastel rainbow pattern
    Query an object space (x, y, z) point

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z position of the point to be queried

    Return:
        (Color) : Calculated color at point
    
    """

    x, y, z = point
    x, y, z = (x+1)/2, (y+1)/2, (z+1)/2
    return Color(int(x*255), int(y*255), int(z*255))

def patternPresent(self, point):
    """
    Pattern function for a ribbon wrapped present
    Query an object space (x, y, z) point

    Args:
        point (tuple[float, float, float]): A tuple containing the x,y,z position of the point to be queried

    Return:
        (Color) : Calculated color at point
    
    Color Args:
        (tuple[Color, Color, float]): Main color, ribbon color, ribbon thickness 
    """

    x, y, z = point
    box_col, stripe_col, stripe_thickness = self.color_args

    if (x >= -(stripe_thickness/2)) and (x <= (stripe_thickness/2)):
        return stripe_col
    if (y >= -(stripe_thickness/2)) and (y <= (stripe_thickness/2)):
        return stripe_col
    
    return box_col



# Union functions - shape
def sdUnionAddition(self, a, b):
    """
    Union function for the Addition of two shapes

    Args:
        a (float): distance to shape a
        b (float): distance to shape b

    Return:
        (float): distance to union

    """

    return min(a, b)

def sdUnionIntersection(self, a, b):
    """
    Union function for the Intersection of two shapes

    Args:
        a (float): distance to shape a
        b (float): distance to shape b

    Return:
        (float): distance to union

    """

    return max(a, b)

def sdUnionSubtraction(self, a, b):
    """
    Union function for subtracting shape b from shape a

    Args:
        a (float): distance to shape a
        b (float): distance to shape b

    Return:
        (float): distance to union

    """

    return max(a, -b)

def sdUnionSmooth(self, a, b):
    """
    Union function for smoothly combining a and b

    Args:
        a (float): distance to shape a
        b (float): distance to shape b

    Return:
        (float): distance to union

    Shape Args:
        (tuple[float]): smoothing factor for the union

    """

    k = 0.5

    h = min(max(0.5 + 0.5*(a - b)/k, 0.0), 1.0)
    dist = ((a*(1-h))+(b*h)) - k*h*(1.0-h)

    return dist


# Union functions - pattern
def patternUnionClosest(self, dist_a, col_a, dist_b, col_b):
    """
    Union function for returning the color of the closest shape

    Args:
        dist_a (float): distance to shape a
        col_a (Color): color of shape a
        dist_b (float): distance to shape b
        col_b (Color): color of shape b

    Return:
        (Color): calculated color
    """

    if (dist_a <= dist_b):
        return col_a
    else:
        return col_b 

def patternUnionSmooth(self, dist_a, col_a, dist_b, col_b):
    """
    Union function for smoothly interpolating between the color of a and b

    Args:
        dist_a (float): distance to shape a
        col_a (Color): color of shape a
        dist_b (float): distance to shape b
        col_b (Color): color of shape b

    Return:
        (Color): calculated color
    
    Pattern Args:
        (tuple[float]): smoothing factor for the union
    """

    k = self.pattern_args[0]

    h = min(max(0.5 + 0.5*(dist_a - dist_b)/k, 0.0), 1.0)


    r = ((col_a.r*(1-h))+(col_b.r*h)) - k*h*(1.0-h)
    g = ((col_a.g*(1-h))+(col_b.g*h)) - k*h*(1.0-h)
    b = ((col_a.b*(1-h))+(col_b.b*h)) - k*h*(1.0-h)

    return Color(int(r), int(g), int(b))

