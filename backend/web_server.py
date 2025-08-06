from abc import ABC
import multiprocessing
from typing import Optional
from pattern_manager import PatternManager
import time
import util
import json
from colors import Color
from attribute import Store, RangeAttr
from tree import tree
from flask import Flask, request, render_template, send_from_directory


class Request(ABC):
    ...

class StopPattern(Request):
    ...

class StartPattern(Request):
    def __init__(self, name: str):
        self.name = name

class DrawFrame(Request):
    def __init__(self, frame: list[tuple[int, int, int] | None]):
        self.frame = frame



class WebServer:
    def __init__(self, rate_limit: bool, patternManager: PatternManager):
        manager = patternManager

        app = Flask(__name__,
                    static_folder='webserver/static',
                    template_folder='webserver/templates'
                    )

        self.app = app
        self.request_queue: multiprocessing.Queue[Request] = multiprocessing.Queue()
        self.process = None

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
            self.request_queue.put_nowait(StartPattern(pattern))
            return render_template('pattern_config.html', pattern=manager.get(pattern), attributes=Store.get_store())

        @app.route('/', methods=['GET'])
        def home():
            return render_template('index.html', patterns=[x for x in manager.patterns.keys()])

        @app.route('/ratelimit.js')
        def serve_js():
            if rate_limit:
                return send_from_directory("webserver/static", "ratelimit.js")
            else:
                return send_from_directory("webserver/static", "nonratelimit.js")

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

    def run(self, port: int):
        self.process = multiprocessing.Process(target=self.app.run, kwargs={"debug":False, "host":"0.0.0.0", "use_reloader":False, "port":int(port)})
        self.process.start()

    def get_next_request(self) -> Optional[Request]:
        if self.request_queue.empty():
            return None
        return self.request_queue.get(False)


