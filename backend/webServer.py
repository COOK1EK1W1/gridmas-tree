import patternManager
import util
import json
from colors import Color
from attribute import store, RangeAttr
from tree import tree
from flask import Flask, request, render_template


def run():
    manager = patternManager.PatternManager("patterns")

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
        util.save_lights(data)
        return "bruh"

    @app.route('/attribute/<nam>', methods=['GET'])
    def attributeG(nam: str):
        a = store.get(nam)
        print(a)
        return str(a.get())

    @app.route('/attribute/<name>', methods=['POST'])
    def attributeS(name: str):
        attribute = store.get(name)
        if isinstance(attribute, RangeAttr):
            attribute.set(float(request.form['value']))
        else:
            attribute.set(Color.fromHex(request.form['value']))
        return "something"

    @app.route('/pattern/<pattern>')
    def pattern(pattern: str):
        if manager.run(pattern):
            return render_template('pattern_config.html', pattern=manager.get(pattern), attributes=store.store)
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
        color = Color.fromHex(value)
        for i in range(tree.num_pixels):
            tree.set_light(i, color)
        tree.update()
        return "bruh"

    return app
