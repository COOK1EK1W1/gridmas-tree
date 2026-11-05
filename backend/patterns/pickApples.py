from tree import tree
from colors import Color, Pixel
from attribute import RangeAttr, ColorAttr
from typing import List, Tuple
import numpy as np
import random


class Apple():
    def __init__(self, color: Color, index):
        self.index = index
        self.color = color
    def set_index(self, index):
        self.index = index
    def get_index(self):
        return self.index
    def get_color(self):
        return self.color

class Picker():
    def __init__(self, color: Color):
        self.color = color
        self.apple = None
    def set_index(self, index):
        self.index = index 
    def get_index(self):
        return self.index
    def get_color(self):
        return self.color
    def set_apple(self, apple: Apple):
        self.apple = apple
    def get_apple(self):
        return self.apple

class Engine():
    def __init__(self):
        tree.set_fps(20)     #default 45
        tree.black()
        self.step = tree.height/30
        self.min_apple_z = tree.height*2/3
        print("================0")

        # init apples
        self.unpicked_apple_list: List[Apple] = []
        self.init_unpicked_apple_list()

        self.picked_apple_list_1: List[Apple] = []       # x>=0, y>=0
        self.picked_apple_list_2: List[Apple] = []       # x<0, y>=0
        self.picked_apple_list_3: List[Apple] = []       # x<0, y<0
        self.picked_apple_list_4: List[Apple] = []       # x>=0, y<0

        print("================1")

        # init space list for picked apple to place
        self.space_list_1: List[int] = []
        self.space_list_2: List[int] = []
        self.space_list_3: List[int] = []
        self.space_list_4: List[int] = []
        self.init_space_list()

        print("================2")

        # init picker
        self.picker = Picker(Color.white())
        self.picker.set_index(self.get_lowest_pixel_index())

        print("================3")


    # TODO
    def get_lowest_pixel_index(self):
        return 0

    def init_unpicked_apple_list(self):
        color_list:List[Color] = []
        color_list.append(Color(139, 0, 0))
        color_list.append(Color(139, 0, 0))
        color_list.append(Color(165, 42, 42))


        for index, pixel in enumerate(tree.pixels):
            if pixel.z >= self.min_apple_z:
                self.unpicked_apple_list.append(Apple(color_list[index%len(color_list)], index))
        
        if len(self.unpicked_apple_list) > 45:
            self.unpicked_apple_list = random.sample(self.unpicked_apple_list, 45)
        


    
    def init_space_list(self):
        index_z_list_1:List[Tuple[int, int]] = []
        index_z_list_2:List[Tuple[int, int]] = []
        index_z_list_3:List[Tuple[int, int]] = []
        index_z_list_4:List[Tuple[int, int]] = []
        
        for index, pixel in enumerate(tree.pixels):
            if pixel.x >= 0 and pixel.y >= 0:
                index_z_list_1.append((index, pixel.z))
            elif pixel.x < 0 and pixel.y >= 0:
                index_z_list_2.append((index, pixel.z))
            elif pixel.x < 0 and pixel.y < 0:
                index_z_list_3.append((index, pixel.z))
            else:
                index_z_list_4.append((index, pixel.z))
        # sort by z
        index_z_list_1 = sorted(index_z_list_1, key=lambda index_z: index_z[1])
        index_z_list_2 = sorted(index_z_list_2, key=lambda index_z: index_z[1])
        index_z_list_3 = sorted(index_z_list_3, key=lambda index_z: index_z[1])
        index_z_list_4 = sorted(index_z_list_4, key=lambda index_z: index_z[1])

        self.space_list_1 = [index_z[0] for index_z in index_z_list_1]
        self.space_list_2 = [index_z[0] for index_z in index_z_list_2]
        self.space_list_3 = [index_z[0] for index_z in index_z_list_3]
        self.space_list_4 = [index_z[0] for index_z in index_z_list_4]

    def run(self):
        self.plan_path()
        print("================4")
        while True:
            if self.update() == False:
                break

    # return False: all apple picked
    def update(self) -> bool:
        self.refresh()

        if self.is_forward_path_completed():
            if self.is_backward_path_completed():
                self.place_apple()
                if len(self.unpicked_apple_list) == 0:
                    print("==============all apple picked! well done!")
                    return False
                else:
                    self.plan_path()
            else:
                if self.is_backward_path_just_start():
                    self.pick_apple()
                self.move_backward()
        else:
            self.move_forward()
        return True

    def refresh(self):
        tree.black()
        # render apples
        for apple in self.unpicked_apple_list:
            tree.get_light(apple.get_index()).set_color(apple.get_color())
        for apple in self.picked_apple_list_1:
            tree.get_light(apple.get_index()).set_color(apple.get_color())
        for apple in self.picked_apple_list_2:
            tree.get_light(apple.get_index()).set_color(apple.get_color())
        for apple in self.picked_apple_list_3:
            tree.get_light(apple.get_index()).set_color(apple.get_color())
        for apple in self.picked_apple_list_4:
            tree.get_light(apple.get_index()).set_color(apple.get_color())

        # render picker
        color = self.picker.get_color()
        apple = self.picker.get_apple()
        if apple != None:
            color = apple.get_color()
        tree.get_light(self.picker.get_index()).set_color(color)


        # for i in range(0, 10):
        #     tree.get_light(self.space_list_1[i]).set_rgb(0, 200, 0)
        #     tree.get_light(self.space_list_2[i]).set_rgb(0, 200, 200)
        #     tree.get_light(self.space_list_3[i]).set_rgb(0, 0, 200)
        #     tree.get_light(self.space_list_4[i]).set_rgb(200, 200, 0)

        tree.update()
    
    def pick_apple(self):
        apple = self.unpicked_apple_list.pop(0)
        self.picker.set_apple(apple)
    
    def place_apple(self):
        apple = self.picker.get_apple()
        pixel = tree.get_light(apple.get_index())
        index = self.picker.get_index()
        apple.set_index(index)
        picked_apple_list = self.get_picked_apple_list(pixel.x, pixel.y)
        picked_apple_list.append(apple)
        self.picker.set_apple(None)
    
    def get_space_list(self, x, y) -> List[int]:
        if x >= 0 and y >= 0:
            return self.space_list_1
        elif x < 0 and y >= 0:
            return self.space_list_2
        elif x < 0 and y < 0:
            return self.space_list_3
        else:
            return self.space_list_4

    def get_picked_apple_list(self, x, y) -> List[int]:
        if x >= 0 and y >= 0:
            return self.picked_apple_list_1
        elif x < 0 and y >= 0:
            return self.picked_apple_list_2
        elif x < 0 and y < 0:
            return self.picked_apple_list_3
        else:
            return self.picked_apple_list_4


    def move_forward(self):
        self.forward_path_index += 1
        self.picker.set_index(self.forward_path[self.forward_path_index])

    def move_backward(self):
        self.backward_path_index += 1
        self.picker.set_index(self.backward_path[self.backward_path_index])

    def is_forward_path_completed(self) -> bool:
        return self.forward_path_index >= len(self.forward_path)-1

    def is_backward_path_completed(self) -> bool:
        return self.backward_path_index >= len(self.backward_path)-1

    def is_backward_path_just_start(self) -> bool:
        return self.backward_path_index == 0

    def plan_path(self):
        self.plan_forward_path()
        self.plan_backward_path()
        
    def plan_forward_path(self):
        apple = self.unpicked_apple_list[0]
        self.forward_path = self.get_path(self.picker.get_index(), apple.get_index(), self.step)
        self.forward_path_index = 0

    def plan_backward_path(self):
        apple = self.unpicked_apple_list[0]
        pixel = tree.get_light(apple.get_index())

        space_list = self.get_space_list(pixel.x, pixel.y)
        space_index = space_list.pop(0)

        self.backward_path = self.get_path(apple.get_index(), space_index, self.step)
        self.backward_path_index = 0

    # return list of indices
    def get_path(self, start_index, end_index, step) -> List[int]:
        path = []
        # print(f"start:{start_index}, end:{end_index}")
        start_pixel = tree.get_light(start_index)
        end_pixel = tree.get_light(end_index)

        points = self.generate_points((start_pixel.x, start_pixel.y, start_pixel.z), (end_pixel.x, end_pixel.y, end_pixel.z), step)
        for i, point in enumerate(points):
            path.append(self.get_nearest_pixel_index(point))

        return path

    def get_nearest_pixel_index(self, point):
        min_distance = 1000
        nearest_index = -1
        for index, pixel in enumerate(tree.pixels):
            cur_point = np.array([pixel.x, pixel.y, pixel.z])
            direction = point - cur_point
            distance = np.linalg.norm(direction)
            if distance < min_distance:
                min_distance = distance
                nearest_index = index

        return nearest_index

    def generate_points(self, start: Tuple[int, int, int], end: Tuple[int, int, int], step: Tuple[int, int, int]):
        start = np.array(start)
        end = np.array(end)
        
        # Calculate the direction vector and normalize it
        direction = end - start
        distance = np.linalg.norm(direction)
        direction_unit = direction / distance  # Unit vector

        points = [start]  # include start point
        current_point = start
        while np.linalg.norm(current_point - start) + step <= distance:
            current_point = current_point + direction_unit * step
            points.append(current_point)

        points.append(end)
        return np.array(points)


name = "PickApples"
author = "Shaocong Lin"

def run():
    engine = Engine()
    engine.run()
