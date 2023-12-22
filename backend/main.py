#!/usr/bin/python3
from flask import Flask, request, json
from util import tree
import util
import time
import spatial_anim
import strip_anim
import threading

app = Flask(__name__)

running_task = None
stop_flag = threading.Event()

pause_time = 0.2


@app.route('/lighton')
def lighton():
    stop_flag.set()
    time.sleep(pause_time)
    stop_flag.clear()
    for i in range(tree.num_pixels):
        tree.set_light(i)
    tree.update()
    return "All On"


@app.route('/lighton/<int:number>')
def lightonN(number: int):
    stop_flag.set()
    time.sleep(pause_time)
    stop_flag.clear()
    tree.set_light(number)
    tree.update()
    return "on"


@app.route('/lightoff')
def lightoff():
    stop_flag.set()
    time.sleep(pause_time)
    stop_flag.clear()
    for i in range(tree.num_pixels):
        tree.set_light(i, (0, 0, 0))
    tree.update()
    return "all off"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
    stop_flag.set()
    time.sleep(pause_time)
    stop_flag.clear()
    tree.set_light(number, (0, 0, 0))
    tree.update()
    return "off"


### animations ###

@app.route('/doXYZ')
def doXYZ():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'xyz'
    threading.Thread(target=spatial_anim.xyz_planes, args=(stop_flag,)).start()
    return "Spin started"


@app.route('/doStrip')
def doStrip():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'strip'
    threading.Thread(target=strip_anim.doStrip, args=(stop_flag,)).start()
    return "standard started"


@app.route('/doTwinkle')
def doTinkle():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'twinkle'
    threading.Thread(target=strip_anim.doTwinkle, args=(stop_flag,)).start()
    return "Tinwkle started"


@app.route('/doSpin')
def doSpin():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'spin'
    threading.Thread(target=spatial_anim.doSpin, args=(stop_flag,)).start()
    return "spin started"


@app.route('/doPlanes')
def doPlanes():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'Planes'
    threading.Thread(target=spatial_anim.doPlanes, args=(stop_flag,)).start()
    return "planes started"


@app.route('/doSphereFill')
def doSphereFill():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'SphereFill'
    threading.Thread(target=spatial_anim.doSphereFill,
                     args=(stop_flag,)).start()
    return "Sphere Fill started"


@app.route('/doRGB')
def doRGB():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'RGB'
    threading.Thread(target=strip_anim.doRGB, args=(stop_flag,)).start()
    return "RGB started"


@app.route('/doWanderingBall')
def doWanderingBall():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'wandering ball'
    threading.Thread(target=spatial_anim.doWanderingBall,
                     args=(stop_flag,)).start()
    return "wandering ball started"


@app.route('/doHueRotate')
def doHueRoatate():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'hue fade'
    threading.Thread(target=strip_anim.doHueRotate,
                     args=(stop_flag,)).start()
    return "hue fade started"

### animations ###


@app.route('/config/setlights', methods=['POST'])
def setLight():
    print(request.data)
    data = json.loads(request.data)
    print(data)
    util.savelights(data)
    return "bruh"

@app.route('/', methods=['GET'])
def home():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Color Picker</title>
</head>
<body>

    <h2>Color Picker</h2>

    <label for="colorPicker">Choose a color:</label>
    <input onChange="sendColor()" type="color" id="colorPicker" name="colorPicker" value="#ff0000">

    <button onChange="sendColor()">Set Light Color</button>
    
    <button onclick="doStrip()">Do strip</button>
    <button onclick="doPlanes()">Do planes</button>
    <button onclick="doSphereFill()">Do spherefill</button>
    <button onclick="doTwinkle()">Do twinkle</button>
    <button onclick="doSpin()">Do spin</button>
    <button onclick="doXYZ()">Do XYZ</button>
    <button onclick="doRGB()">Do RGB</button>
    <button onclick="doHueRotate()">Do Hue Rotate</button>
    <button onclick="doWanderingBall()">Do Wanding Ball</button>

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

        function doStrip() {
            sendRequest("http://192.168.1.50/doStrip");
        }
        function doPlanes() {
            sendRequest("http://192.168.1.50/doPlanes");
        }
        function doSphereFill() {
            sendRequest("http://192.168.1.50/doSphereFill");
        }
        function doTwinkle() {
            sendRequest("http://192.168.1.50/doTwinkle");
        }
        function doSpin() {
            sendRequest("http://192.168.1.50/doSpin");
        }

        function doXYZ() {
            sendRequest("http://192.168.1.50/doXYZ");
        }

        function doRGB() {
            sendRequest("http://192.168.1.50/doRGB");
        }

        function doHueRotate() {
            sendRequest("http://192.168.1.50/doHueRotate");
        }

        function doWanderingBall() {
            sendRequest("http://192.168.1.50/doWanderingBall");
        }

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
    stop_flag.set()
    time.sleep(pause_time)
    stop_flag.clear()
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
    app.run(debug=True, host="0.0.0.0", use_reloader=False, port =80)
