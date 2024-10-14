from pattern_manager import PatternManager
import time
import util
import json
from colors import Color
from attribute import Store, RangeAttr
from tree import tree
from flask import Flask, request, render_template


def init():
    manager = PatternManager("patterns")

    app = Flask(__name__)

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
        tree.black()
        tree.update()
        return "all off"

    @app.route('/setalllight', methods=['POST'])
    def setLightColor():
        data = json.loads(request.data)
        for color, pixel in zip(data, tree.pixels):
            pixel.set_rgb(color[0], color[1], color[2])
        tree.update()
        return "done"

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
        util.save_lights(data)
        return "bruh"

    @app.route('/attribute/<nam>', methods=['GET'])
    def attributeG(nam: str):
        a = Store.get_store().get(nam)
        print(a)
        return str(a.get())

    @app.route('/attribute/<name>', methods=['POST'])
    def attributeS(name: str):
        attribute = Store.get_store().get(name)
        if isinstance(attribute, RangeAttr):
            attribute.set(float(request.form['value']))
        else:
            attribute.set(Color.from_hex(request.form['value']))
        return "something"

    @app.route('/pattern/<pattern>')
    def pattern(pattern: str):
        if manager.queue_pattern(pattern):
            time.sleep(0.1)
            return render_template('pattern_config.html', pattern=manager.get(pattern), attributes=Store.get_store())
        else:
            return "not running"

    @app.route('/', methods=['GET'])
    def home():
        return render_template('index.html', patterns=manager.patterns)

    @app.route('/setlights', methods=['POST'])
    def setLights():
        print("setting lights")
        print(request.data)
        data = json.loads(request.data)

        value = data["color"]
        color = Color.from_hex(value)
        for i in range(tree.num_pixels):
            tree.set_light(i, color)
        tree.update()
        return "bruh"

    return app
