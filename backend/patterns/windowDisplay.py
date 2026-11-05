import cv2
import mss
import numpy as np
import pygetwindow as gw
from tree import tree

name = "Window on Tree"
author = "Aiden Ruz"

def run():
    # Find a window using pygetwindow
    window_title = input("Enter the name of the window you would like to view on the tree: ")
    window = None
    for window_check in gw.getWindowsWithTitle(window_title):
        if window_title in window_check.title:  # Search for window matching with chosen title
            window = window_check
            break

    if not window:
        print(window_title + " was not found. Please ensure a windowed instance of an application containing the name " + window_title + " is running.")
        return

    # Define monitor for mss to capture chosen window coordinates
    monitor = {
        "top": window.top,
        "left": window.left,
        "width": window.width,
        "height": window.height
    }
    
    with mss.mss() as sct:
        while True:
            # Capture the chosen window
            frame = np.array(sct.grab(monitor))
            
            # Check if frame is a numpy array
            if not isinstance(frame, np.ndarray):
                print("Frame capture failed, skipping this frame.")
                continue
            
            # Convert BGRA to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

            # Resize the captured frame to match LED tree resolution
            resized_frame = cv2.resize(frame_rgb, (monitor["width"], monitor["height"]))

            # Map the frame pixels to the tree LEDs
            coords = []
            for pixel in tree.pixels:
                videox = max(min(int(((-pixel.x + 1) / 2) * monitor["width"]), monitor["width"] - 1), 0)
                videoy = max(min(int((1 - pixel.z / 2) * monitor["height"]), monitor["height"] - 1), 0)
                coords.append((videox, videoy))
                
                r, g, b = resized_frame[videoy, videox]
                
                # Ensure values are scaled correctly
                b, g, r = [min(max(int(c * (255 / 255)), 0), 255) for c in (b, g, r)]

                # Check if the color is too dark (close to black)
                if r <= 5 and g <= 5 and b <= 5:
                    pixel.set_rgb(0, 0, 0)  # Turn off for very dark colors
                else:
                    pixel.set_rgb(r, g, b)  # Set the RGB value otherwise

            # Update the tree display
            tree.update()