#!/usr/bin/python3
from flask import Flask, request, json

from util import tree

import util
from pattern import load_patterns
import time
import killableThread
from attribute import store
import json

app = Flask(__name__)

running_task: None|killableThread.Thread = None


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

@app.route('/attribute/<nam>', methods=['GET'])
def attributeG(nam: str):
    a = store.get(nam)
    print(a)
    return str(a.get())

@app.route('/attribute/<name>', methods=['POST'])
def attributeS(name: str):
    print(request.data)
    print(request.get_json()['speed'])
    store.set(name, request.get_json()['speed'])
    return "something"



@app.route('/pattern/<pattern>')
def pattern(pattern: str):
    global running_task
    apattern = list(filter(lambda x: x.name == pattern, patterns))
    if len(apattern) > 0:
        if running_task:
            running_task.terminate()
        running_task = killableThread.Thread(target=apattern[0].run)
        running_task.start()
        print([x for x in store])
        return "running"
    else:
        return "not running"


def button(fn, name):
    return f'<button class="m-2 py-4 bg-blue-200 p-2 rounded-xl w-96 shadow-lg border-2 border-blue-500" onclick="{fn}()">{name}</button>'


def fn(fn):
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

    <button onClick="test(0.2)">Set Light Color</button>
    <button onClick="test(1)">Set Light Color</button>
    <button onClick="test(3)">Set Light Color</button>

    <div class="flex flex-wrap w-full m-2 justify-center">
    """ + "\n".join(map(lambda x: button(x.name, x.display_name), patterns)) + """
    </div>
    <script>
        function test(a){

            var xhr = new XMLHttpRequest();
            xhr.open("POST", "attribute/sleep%20time", true);
            xhr.setRequestHeader("Content-Type", "application/json");

            var data = JSON.stringify({ speed: a });

            xhr.onreadystatechange = function () {
                if (xhr.readyState == 4 && xhr.status == 200) {
                    console.log("Color set successfully");
                } else if (xhr.readyState == 4) {
                    console.error("Error setting color");
                }
            };

            xhr.send(data);
        }

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
        """ + " ".join(map(lambda x: fn(x.name), patterns)) + """


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
    app.run(debug=True, host="0.0.0.0", use_reloader=False, port=3000)
