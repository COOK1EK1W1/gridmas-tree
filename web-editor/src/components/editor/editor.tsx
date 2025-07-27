"use client"
import CodeEditor from "./code";
import { PyodideInterface } from "pyodide";
import TreeVis from "./treevis";
import { useEffect, useState } from "react";
import { useEditor } from "@/util/context/editorContext";
import TopBar from "./topBar";

export default function PatternEditor() {
  const { codeRef, setLights } = useEditor()



  const [pyodide, setPyodide] = useState<PyodideInterface | null>(null);
  const [output, setOutput] = useState("");
  const [running, setRunning] = useState(false);
  const [loop, setLoop] = useState<any>(null);
  const [loopTimes, setLoopTimes] = useState<number[]>([])

  // Load Pyodide when the component mounts
  useEffect(() => {
    const loadPyodide = async () => {
      const pyodideInstance = await window.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
      });
      setPyodide(pyodideInstance);
      pyodideInstance.FS.mkdir("pixel_driver");
      ["util.py", "colors.py", "tree.csv", "treeTest.py", "prelude.py", "tree.py", "particle_system.py"].map((x) => {
        fetch(`${process.env.NEXT_PUBLIC_BASEURL}/api/send-script?s=${x}`).then((res) =>
          res.text().then(res2 => {
            console.log(res2)
            pyodideInstance.FS.writeFile(x, res2)
          })
        )
      })
    };

    loadPyodide();
  }, []);


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
        setOutput("")
      } catch (error: any) {
        setRunning(false)
        setOutput(error.toString());
      }
    } else {
      setOutput("Pyodide is still loading...");
    }
  }

  // if we see running change
  useEffect(() => {
    if (running) {
      if (pyodide == null) {
        setOutput("bruh")
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
          setOutput(error.toString())
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
      <div className="w-1/2 h-full">
        <div className="h-[50dvh] bg-black">
          <TreeVis />

        </div>
        <button onClick={handleRun} className={`cursor-pointer bg-slate-800 w-28 py-1 rounded-xl m-2 ${running ? "bg-green" : ""}`}>{!running ? "run" : "stop"}</button>
        <p>{(loopTimes.reduce((a, b) => a + b, 0) / loopTimes.length).toFixed(2)}ms / 22ms</p>
        <div>{output}</div>
      </div>
      <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
    </div >
  );
}
