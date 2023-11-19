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

running_task = None
stop_flag = threading.Event()


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


@app.route('/doCool')
def docoool():
    global running_task
    stop_flag.set()
    time.sleep(2)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'spin'
    threading.Thread(target=spatial_anim.xyz_planes, args=(stop_flag,)).start()
    return "Spin started"


@app.route('/doStandard')
def doStandarda():
    global running_task
    stop_flag.set()
    time.sleep(2)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'standard'
    threading.Thread(target=strip_anim.doStandard, args=(stop_flag,)).start()
    return "standard started"


@app.route('/doTwinkle')
def doTinklee():
    global running_task
    stop_flag.set()
    time.sleep(2)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'twinkle'
    threading.Thread(target=strip_anim.doTwinkle, args=(stop_flag,)).start()
    return "Tinwkle started"


@app.route('/doSpin')
def doSpin():
    global running_task
    stop_flag.set()
    time.sleep(2)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'spin'
    threading.Thread(target=spatial_anim.doSpin, args=(stop_flag,)).start()
    return "spin started"


@app.route('/config/setlights', methods=['POST'])
def setLight():
    print(request.data)
    data = json.loads(request.data)
    print(data)
    util.savelights(data)
    return "bruh"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
