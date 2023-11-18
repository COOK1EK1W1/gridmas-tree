from flask import Flask, request, json
from util import turnOffLight, turnOnLight, doCool, savelights, update, doStandard, doSpin
import os
from dotenv import load_dotenv

app = Flask(__name__)


load_dotenv()

@app.route('/lighton')
def lighton():
    for i in range(int(os.getenv("PIXELS"))):
        turnOnLight(i)
    update()
    return "bruh"


@app.route('/lighton/<int:number>')
def lightonN(number: int):
    turnOnLight(number)
    update()
    return "bruh"


@app.route('/lightoff')
def lightoff():
    for i in range(int(os.getenv("PIXELS"))):
        turnOffLight(i)
    update()
    return "bruh"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
    turnOffLight(number)
    update()
    return "bruh"


@app.route('/doCool/<int:number>')
def docoool(number: int):
    doCool(number)
    return "bruh"

@app.route('/doSpin')
def dospin():
    doSpin()
    return "bruh"

@app.route('/doStandard/<int:number>')
def doStandarda(number: int):
    doStandard(number)
    return "bruh"

@app.route('/config/setlights', methods=['POST'])
def setLight():
    print(request.data)
    data = json.loads(request.data)
    print(data)
    savelights(data)
    return "bruh"



if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
