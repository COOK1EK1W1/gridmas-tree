# :material-pine-tree: Homepage

Welcome to the official home of documentation for the GRIDmas Tree project. On this site you will find all the information that you will need to make your own customised designs and patterns for the Tree.

This is a project based on Standup Maths' 500 LED christmas tree [Watch Here](https://www.youtube.com/watch?v=TvlpIojusBE)

---

# :material-run: How To Run
To run this project you must have `Python` installed on your system.

## :material-download: Downloading
To download the Gridmas tree code you can either use the github Desktop app to clone the code or use git from the terminal as below

``` git
git clone https://github.com/COOK1EK1W1/gridmas-tree.git
```

## Setup
The project comes with a virtual environment (venv) setup script. Using this is optional but recommended.

### Venv
To set up a venv, run the following commands. If you are not setting up a venv, proceed to Installing Modules

#### :material-microsoft-windows: Windows
```
venv/Scripts/activate.bat
```
#### :simple-linux: Linux
``` shell
source venv/Scripts/activate
```

#### :simple-apple: Mac
``` shell
source venv/Scripts/activate
```

### Installing Modules
To install the modules required for the project to work run the following command

```
pip install -r requirements.txt
```

### Running
Now that the project has been setup, you are ready to run it.

To run the tree simulator, run the following commands

``` shell
cd backend

python main.py
```

This will start the webserver, and - assuming that you don't have 1000 LEDs connected, because who doesn't? - will start the tree simulator program.

Once the webserver is up and running, you should be able to access the tree controller at [This address](http://localhost:3000). (http://localhost:3000)
