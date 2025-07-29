"use client"
import CodeEditor from "./code";
import { PyodideInterface } from "pyodide";
import TreeVis from "./treevis";
import { useEffect, useRef, useState } from "react";
import { useEditor } from "@/util/context/editorContext";
import TopBar from "./topBar";
import { Button } from "../ui/button";

export default function PatternEditor() {
  const { codeRef, setLights } = useEditor()



  const [pyodide, setPyodide] = useState<PyodideInterface | null>(null);
  const [output, setOutput] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [loop, setLoop] = useState<any>(null);
  const [loopTimes, setLoopTimes] = useState<number[]>([])
  const bottomRef = useRef<HTMLDivElement | null>(null);

  function appendOutput(x: string) {
    setOutput((prev) => {
      const a = [...prev, x]
      if (a.length > 200) {
        a.shift()
      }
      return a
    })
  }

  useEffect(() => {
    // Scrolls to the bottom every time messages change
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [output]);

  // Load Pyodide when the component mounts
  useEffect(() => {
    const loadPyodide = async () => {
      const pyodideInstance = await window.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
      });
      pyodideInstance.globals.set("print_to_react", appendOutput);
      setPyodide(pyodideInstance);

      // load all the core libraries
      pyodideInstance.FS.mkdir("pixel_driver");
      ["util.py", "colors.py", "tree.csv", "treeTest.py", "prelude.py", "tree.py", "particle_system.py"].map((x) => {
        fetch(`${process.env.NEXT_PUBLIC_BASEURL}/api/send-script?s=${x}`).then((res) =>
          res.text().then(res2 => {
            console.log(res2)
            pyodideInstance.FS.writeFile(x, res2)
          })
        )
      })
      pyodideInstance.runPython(`import sys

class JSWriter:
    def write(self, s):
        if s.strip():
            print_to_react(s)

    def flush(self):
        pass

sys.stdout = JSWriter()
sys.stderr = JSWriter()`)
    };

    loadPyodide();
  }, []);

  //update the pattern in the filesystem
  function handleUpdate() {
    // we want to start running
    if (pyodide && codeRef.current) {
      try {
        pyodide.FS.writeFile("curPattern.py", `from prelude import *
` + codeRef.current.getValue())
        pyodide.runPython(`import curPattern
import prelude
from tree import tree
import importlib
importlib.reload(curPattern)
`)
      } catch (error: any) {
        setRunning(false)
        setOutput([error.toString()]);
      }
    } else {
      setOutput(["Pyodide is still loading..."]);
    }
  }

  function handleRun() {
    // stop running 
    if (running) {
      setRunning(false);
      return
    }

    // we want to start running
    if (pyodide && codeRef.current) {
      try {
        pyodide.FS.writeFile("curPattern.py", `from prelude import *
` + codeRef.current.getValue())
        pyodide.runPython(`import curPattern
import prelude
from tree import tree
import importlib
importlib.reload(curPattern)
`)
        setRunning(true)
        setOutput([])
      } catch (error: any) {
        setRunning(false)
        setOutput([error.toString()]);
      }
    } else {
      setOutput(["Pyodide is still loading..."]);
    }
  }

  // if we see running change
  useEffect(() => {
    if (running) {
      if (pyodide == null) {
        return
      }
      setLoop(setInterval(() => {
        const start = performance.now()
        try {
          const res = pyodide.runPython(`
curPattern.draw()
list(map(lambda x: [x.to_tuple()[0] / 255, x.to_tuple()[1] / 255, x.to_tuple()[2] / 255], tree.request_frame()))
`)
          setLights(res.toJs())
        } catch (error: any) {
          setRunning(false)
          appendOutput(error.toString())
        }
        const end = performance.now()
        setLoopTimes((a) => {
          a.push(end - start)
          if (a.length > 20) {
            a.shift()
          }
          return a
        })
      }, 22))
    } else {
      clearInterval(loop)

    }
  }, [running])

  return (
    <div className="h-full flex flex-row">
      <div className="w-1/2 bg-slate-200 h-full">
        <TopBar />
        <CodeEditor />
      </div>
      <div className="w-1/2 h-screen flex flex-col">
        <div className="flex-grow">
          <TreeVis />
        </div>
        <div className="h-52">
          <div className="h-12">
            <Button className="w-28 m-2" onClick={handleRun}>{!running ? "Run" : "Stop"}</Button>
            <Button className="w-28 m-2" onClick={handleUpdate}>Update</Button>
            <span className="w-28 m-2">{(loopTimes.reduce((a, b) => a + b, 0) / loopTimes.length).toFixed(2)}ms / 22ms</span>
          </div>
          <div className="h-40 overflow-auto">{output.map((x, i) => (
            <p key={i} className={`px-2 font-mono ${i % 2 == 0 ? "bg-slate-100" : "bg-slate-200"}`}>
              {x}
            </p>


          ))}
            <div ref={bottomRef} />
          </div>
        </div>
      </div>
      <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
    </div >
  );
}
