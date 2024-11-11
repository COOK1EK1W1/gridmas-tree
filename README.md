# Gridmas tree
This is a project based on Standup Maths' 500 LED christmas tree https://www.youtube.com/watch?v=TvlpIojusBE

# Docs
Still in progress: [Docs](https://ciarancook.com/gridmastree-docs)

# How To Run
## Downloading
To download the Gridmas tree code you can either use the github Desktop app to clone the code or use git from the terminal as below

```
git clone https://github.com/COOK1EK1W1/gridmas-tree.git
```

## Setup
The project comes with a virtual environment (venv) setup script. Using this is optional but recommended.

### Venv
To set up a venv, run the following commands. If you are not setting up a venv, proceed to Installing Modules

```
python -m venv venv

[WINDOWS ONLY]
venv/Scripts/activate.bat

[MAC/LINUX ONLY]
source venv/bin/activate
```

### Installing Modules
To install the modules required for the project to work run the following command

```
pip install -r requirements.txt
```

### Running
Now that the project has been setup, you are ready to run it.

To run the tree simulator, run the following commands

```
cd backend

python main.py
```

This will start the webserver, and - assuming that you don't have 1000 LEDs connected, because who doesn't? - will start the tree simulator program.

Once the webserver is up and running, you should be able to access the tree controller at [This address](http://localhost:3000). (http://localhost:3000)
