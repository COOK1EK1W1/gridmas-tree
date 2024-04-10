#!/usr/bin/python3
from flask import Flask, request, json

from util import tree

import util
from pattern import load_patterns
import time
import multiprocessing

app = Flask(__name__)

running_task = None


pattern_dir = "patterns"
patterns = load_patterns(pattern_dir)


@app.route('/lighton')
def lighton():
    for i in range(tree.num_pixels):
        tree.set_light(i)
    tree.update()
    return "All On"


@app.route('/lighton/<int:number>')
def lightonN(number: int):
    tree.set_light(number)
    tree.update()
    return "on"


@app.route('/lightoff')
def lightoff():
    for i in range(tree.num_pixels):
        tree.set_light(i, (0, 0, 0))
    tree.update()
    return "all off"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
    tree.set_light(number, (0, 0, 0))
    tree.update()
    return "off"


@app.route('/config/setlights', methods=['POST'])
def setLight():
    print(request.data)
    data = json.loads(request.data)
    print(data)
    util.savelights(data)
    return "bruh"


@app.route('/pattern/<pattern>')
def pattern(pattern: str):
    global running_task
    apattern = list(filter(lambda x: x.name == pattern, patterns))
    if len(apattern) > 0:
        if running_task:
            running_task.terminate()
        running_task = multiprocessing.Process(target=apattern[0].run)
        running_task.start()
        return "running"
    else:
        return "not running"


def button(fn, name):
    return f'<button class="m-2 py-4 bg-blue-200 p-2 rounded-xl w-96 shadow-lg border-2 border-blue-500" onclick="{fn}()">{name}</button>'


def fn(fn, name):
    return """
        function """ + fn + """() {
            sendRequest("/pattern/""" + fn + """");
        }"""


@app.route('/', methods=['GET'])
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Color Picker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body>

    <h2>Color Picker</h2>

    <label for="colorPicker">Choose a color:</label>
    <input onChange="sendColor()" type="color" id="colorPicker" name="colorPicker" value="#ff0000">

    <button onChange="sendColor()">Set Light Color</button>

    <div class="flex flex-wrap w-full m-2 justify-center">
    """ + "\n".join(map(lambda x: button(x.name, x.display_name), patterns)) + """
    </div>
    <script>

        function sendColor() {
            var selectedColor = document.getElementById("colorPicker").value;

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "http://192.168.1.50/setlights", true);
            xhr.setRequestHeader("Content-Type", "application/json");

            var data = JSON.stringify({ color: selectedColor });

            xhr.onreadystatechange = function () {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    console.log("Color set successfully");
                } else if (xhr.readyState == 4) {
                    console.error("Error setting color");
                }
            };

            xhr.send(data);
        }
        """ + " ".join(map(lambda x: fn(x.name, x.name), patterns)) + """


        function sendRequest(url) {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", url, true);

            xhr.onreadystatechange = function () {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    console.log("Request sent successfully");
                } else if (xhr.readyState == 4) {
                    console.error("Error sending request");
                }
            };

            xhr.send();
        }
    </script>

</body>
</html>
"""


@app.route('/setlights', methods=['POST'])
def setLights():
    print("setting lights")
    time.sleep(pause_time)
    print(request.data)
    data = json.loads(request.data)
    print(data)

    value = data["color"]
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    print(rgb)
    for i in range(tree.num_pixels):
        tree.set_light(i, rgb)
    tree.update()
    return "bruh"


def wipe_on():
    for rng in range(0, int(tree.height*200), 10):
        for i in range(len(tree.pixels)):
            if rng <= tree.coords[i][2]*200 < rng + 10:
                tree.set_light(i, (200, 55, 2))
        tree.update()
        time.sleep(1/45)


if __name__ == '__main__':
    wipe_on()
    app.run(debug=True, host="0.0.0.0", use_reloader=False, port=80)


def a():
    i = 0
    while True:
        pattern_thread = multiprocessing.Process(target=patterns[i].run)
        pattern_thread.start()
        time.sleep(10)
        pattern_thread.terminate()
        i = (i + 1) % len(patterns)
