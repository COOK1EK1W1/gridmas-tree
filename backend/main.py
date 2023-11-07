from flask import Flask
from util import turnOffLight, turnOnLight

app = Flask(__name__)


@app.route('/lighton')
def lighton():
    print("turn all on")
    return "bruh"


@app.route('/lighton/<int:number>')
def lightonN(number: int):
    turnOnLight(number)
    return "bruh"


@app.route('/lightoff')
def lightoff():
    print("turn all off")
    return "bruh"


@app.route('/lightoff/<int:number>')
def lightoffN(number: int):
    turnOffLight(number)
    return "bruh"


if __name__ == '__main__':
    app.run(debug=True)
