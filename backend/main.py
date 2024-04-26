#!/usr/bin/python3
from flask import Flask, request, render_template

from util import tree

import util
from pattern import load_patterns
import time
import killableThread
from attribute import store
from colors import Color
import json

app = Flask(__name__)

running_task: None | killableThread.Thread = None


pattern_dir = "patterns"
patterns = load_patterns(pattern_dir)


@app.route('/lighton')
def lighton():
    for i in range(tree.num_pixels):
        tree.set_light(i, Color.white())
    tree.update()
    return "All On"


@app.route('/lighton/<int:number>')
def lightonN(number: int):
    tree.set_light(number, Color.white())
    tree.update()
    return "on"


@app.route('/lightoff')
def lightoff():
    for i in range(tree.num_pixels):
        tree.set_light(i, Color.black())
    tree.update()
    return "all off"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
    tree.set_light(number, Color.black())
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
    print(request.form)
    print(request.form['value'])
    store.set(name, float(request.form['value']))
    return "something"


@app.route('/pattern/<pattern>')
def pattern(pattern: str):
    global running_task
    apattern = list(filter(lambda x: x.name == pattern, patterns))
    if len(apattern) > 0:
        if running_task:
            running_task.terminate()
        store.reset()
        running_task = killableThread.Thread(target=apattern[0].run)
        running_task.start()
        time.sleep(0.1)
        print(store.store)
        return render_template('pattern_config.html', pattern=apattern[0], attributes=store.store)
    else:
        return "not running"


@app.route('/', methods=['GET'])
def home():
    return render_template('index.html', patterns=patterns)


@app.route('/setlights', methods=['POST'])
def setLights():
    print("setting lights")
    print(request.data)
    data = json.loads(request.data)
    print(data)

    value = data["color"]
    color = Color.fromHex(value)
    for i in range(tree.num_pixels):
        tree.set_light(i, color)
    tree.update()
    return "bruh"


def wipe_on():
    for rng in range(0, int(tree.height * 200), 10):
        for i in range(len(tree.pixels)):
            if rng <= tree.coords[i][2] * 200 < rng + 10:
                tree.set_light(i, Color(200, 55, 2))
        tree.update()
        time.sleep(1 / 45)


if __name__ == '__main__':
    wipe_on()
    app.run(debug=True, host="0.0.0.0", use_reloader=False, port=3000)
