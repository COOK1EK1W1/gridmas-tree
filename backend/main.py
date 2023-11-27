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
    stop_flag.set()
    time.sleep(pause_time)
    stop_flag.clear()
    for i in range(tree.num_pixels):
        tree.set_light(i, (0, 0, 0))
    tree.update()
    return "all off"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
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
def doRGB():
    global running_task
    stop_flag.set()
    time.sleep(pause_time)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'wandering ball'
    threading.Thread(target=spatial_anim.doWanderingBall,
                     args=(stop_flag,)).start()
    return "wandering ball started"

### animations ###


@app.route('/config/setlights', methods=['POST'])
def setLight():
    print(request.data)
    data = json.loads(request.data)
    print(data)
    util.savelights(data)
    return "bruh"


def wipe_on():
    for rng in range(0, int(tree.height*200), 10):
        for i in range(len(tree.pixels)):
            if rng <= tree.coords[i][2]*200 < rng + 10:
                tree.set_light(i, (40, 200, 10))
        tree.update()
        time.sleep(1/45)


if __name__ == '__main__':
    wipe_on()
    app.run(debug=True, host="0.0.0.0", use_reloader=False)
