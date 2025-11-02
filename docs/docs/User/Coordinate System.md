GRIDmas Tree Coordinate System

GRIDmas Tree uses GIFT for it's coordinate system. That is, Geographical Information For Trees. For a full in-depth explanation, find Matt Parkers video on his tree [Here](https://youtu.be/WuMRJf6B5Q4?si=hVqUVpmA2eyl7wWS&t=2061)

# How does G.I.F.T work?
The GIFT system starts at -1 and ends at 1 in the `x` and `y` axes. In the Z axis it goes from 0 to a maximum number.
The axes are as follows:

* `x`: The axis that goes towards the camera when the tree loads
* `y`: The axis that goes from left, to right when the camera loads
* `z`: The up/down axis.


The origin of the tree (position 0,0,0) is set to be the centre of the trunk. This means that when the editor loads, any `-y` values will be LEDs on the left hand side of the tree, and any `+y` values will be LEDs on the right hand side. Similarly, any `-x` values will be further away from the view, and any `+x` values will be closer.