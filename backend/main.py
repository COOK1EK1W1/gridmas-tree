from flask import Flask, request, json
import util
import time
import spatial_anim
import strip_anim
import threading
import os
from dotenv import load_dotenv

app = Flask(__name__)

running_task = None
stop_flag = threading.Event()

load_dotenv()

num_pixels = os.getenv("PIXELS")
if num_pixels == None:
    raise Exception("No pixels env variable")
num_pixels = int(num_pixels)

running_task = None
stop_flag = threading.Event()


@app.route('/lighton')
def lighton():
    for i in range(num_pixels):
        util.setLight(i)
    util.update()
    return "bruh"


@app.route('/lighton/<int:number>')
def lightonN(number: int):
    util.setLight(number)
    util.update()
    return "bruh"


@app.route('/lightoff')
def lightoff():
    for i in range(num_pixels):
        util.turnOffLight(i)
    util.update()
    return "bruh"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
    util.turnOffLight(number)
    util.update()
    return "bruh"


@app.route('/doCool')
def docoool():
    global running_task
    stop_flag.set()
    time.sleep(2)  # Allow time for the task to stop
    stop_flag.clear()
    running_task = 'spin'
    threading.Thread(target=spatial_anim.xyz_planes, args=(stop_flag,)).start()
    return "Spin started"


@app.route('/doSpin')
def dospin():
    util.doSpin()
    return "bruh"


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

@app.route('/config/setlights', methods=['POST'])
def setLight():
    print(request.data)
    data = json.loads(request.data)
    print(data)
    util.savelights(data)
    return "bruh"


if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
