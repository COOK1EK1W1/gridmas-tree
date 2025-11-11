from abc import ABC
import threading
from typing import Optional
from pattern_manager import PatternManager
import util
import json
import time
from flask import Flask, request, render_template, send_from_directory
from queue import Queue
from gridmas import *


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
        self.request_queue: Queue[Request] = Queue()
        self.thread = None
        self.should_stop = False


        ## util lights

        @app.route('/lighton')
        def lighton():
            frame = DrawFrame([(255, 255, 255) for _ in range(num_pixels())])
            self.request_queue.put(frame)
            return "All On"

        @app.route('/lighton/<int:number>')
        def lightonN(number: int):
            frame = DrawFrame([(255, 255, 255) if i == number else None for i in range(num_pixels())])
            self.request_queue.put(frame)
            return "on"

        @app.route('/lightoff')
        def lightoff():
            frame = DrawFrame([(0, 0, 0) for _ in range(num_pixels())])
            self.request_queue.put(frame)
            return "all off"

        @app.route('/setalllight', methods=['POST'])
        def setLightColor():
            data = json.loads(request.data)
            frame = []
            for color in data:
                frame.append((color[0], color[1], color[2]))
            self.request_queue.put(frame)
            return "done"

        @app.route('/lightoff/<int:number>')
        def lightoffN(number: int):
            frame = DrawFrame([(0, 0, 0) if i == number else None for i in range(num_pixels())])
            self.request_queue.put(frame)
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
            return str(a.get())

        @app.route('/attribute/<name>', methods=['POST'])
        def attributeS(name: str):
            attribute = Store.get_store().get(name)
            if isinstance(attribute, RangeAttr):
                attribute.set(float(request.form['value']))
            else:
                attribute.set(Color.hex(request.form['value']))
            return "something"

        @app.route('/pattern/<pattern>')
        def pattern(pattern: str):
            self.request_queue.put(StartPattern(pattern))
            time.sleep(0.1)
            return render_template('pattern_config.html', pattern=manager.get(pattern), attributes=Store.get_store())


        @app.route('/setlights', methods=['POST'])
        def setLights():
            print("setting lights")
            print(request.data)
            data = json.loads(request.data)

            value = data["color"]
            color = Color.hex(value)
            for i in range(num_pixels()):
                tree.set_light(i, color)
            tree.update()
            return "bruh"


        ## Web interface

        @app.route('/', methods=['GET'])
        def home():
            return render_template('index.html', patterns=[x for x in manager.patterns.keys()])

        @app.route('/ratelimit.js')
        def serve_js():
            if rate_limit:
                return send_from_directory("webserver/static", "ratelimit.js")
            else:
                return send_from_directory("webserver/static", "nonratelimit.js")


    def run(self, port: int):
        def run_flask():
            self.app.run(debug=False, host="0.0.0.0", use_reloader=False, port=port)
        
        self.thread = threading.Thread(target=run_flask, daemon=True)
        self.thread.start()

    def get_next_request(self) -> Optional[Request]:
        try:
            return self.request_queue.get_nowait()
        except:
            return None

    def stop(self):
        self.should_stop = True
        if self.thread and self.thread.is_alive():
            # Note: Flask doesn't have a clean shutdown method in this context
            # The daemon thread will be cleaned up when the main process exits
            pass


