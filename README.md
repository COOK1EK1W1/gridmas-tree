# Gridmas Tree - Web
This is a project based on Standup Maths' 500 LED christmas tree. [Watch his video here](https://www.youtube.com/watch?v=TvlpIojusBE)

# Docs
Documentation for the web edition can be found through the button labeled `Reference` on the homepage, and from the `/reference` section of the website.

# How To Setup
## Downloading
To download the Gridmas Tree web editor you can use any of the below tools:
- [GitHub desktop app](https://desktop.github.com/download/)
    ![Opening with the GitHub desktop app](OpenWithGithubDesktop.png)
- [Git](https://git-scm.com/downloads)
    ```bash
    git clone https://github.com/COOK1EK1W1/gridmas-tree.git
    ```
- [GitHub CLI](https://cli.github.com/)
    ```bash
    gh repo clone COOK1EK1W1/gridmas-tree
    ```

## Setup
Now that you have the project downloaded, you a ready to install the project dependencies.
It is recommended to use the [NPM Bun](https://www.npmjs.com/package/bun) package for running the project. 

To install the dependencies:
```bash
bun i
```
Now wait for the dependencies to be installed.

## Run
To run the project, run the below command:
```bash
bun run dev
```

This will start a local web server which you can access. There will be an IP address echo'd in your terminal, _copy/paste_ it into your browser of choice to see the web view