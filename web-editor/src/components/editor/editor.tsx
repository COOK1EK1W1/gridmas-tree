"use client"
import CodeEditor from "./code";
import TreeVis from "./treevis";
import { useEffect, useRef, useState } from "react";
import { useEditor } from "@/util/context/editorContext";
import TopBar from "./topBar";
import { Button } from "../ui/button";
import { usePyodide } from "@/util/usePyodide";

type Message = {
  content: string,
  error: boolean,
  frame: number
}

export default function PatternEditor() {
  const { codeRef, setLights } = useEditor()
  const { pyodide, loading } = usePyodide();

  const [output, setOutput] = useState<Message[]>([]);
  const [running, setRunning] = useState(false);
  const [loopTimes, setLoopTimes] = useState<number[]>([])
  const bottomRef = useRef<HTMLDivElement | null>(null);

  function appendOutput(x: string, frame: number) {
    setOutput((prev) => {
      const a = [...prev, { content: x, frame: frame, error: false }]
      // split the output to 200 lines so we get that buttery smooth scroll
      if (a.length > 400) {
        return a.slice(200, 200)
      }
      return a
    })
  }

  useEffect(() => {
    // Scrolls to the bottom every time messages change
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [output]);

  // Initialize Pyodide when it's loaded
  useEffect(() => {
    if (pyodide && !loading) {
      pyodide.globals.set("print_to_react", appendOutput);

      // load all the core libraries
      ["util.py", "colors.py", "tree.csv", "prelude.py", "tree.py", "particle_system.py"].map((x) => {
        fetch(`${process.env.NEXT_PUBLIC_BASEURL}/api/send-script?s=${x}`).then((res) =>
          res.text().then(res2 => {
            pyodide.FS.writeFile(x, res2)
          })
        )
      })
      pyodide.runPython(`import sys

class JSWriter:
    def write(self, s):
        if s.strip():
            print_to_react(s, 0)

    def flush(self):
        pass

sys.stdout = JSWriter()
sys.stderr = JSWriter()`)
    }
  }, [pyodide, loading]);

  // Helper function to update the pattern
  function updatePattern() {
    if (!pyodide || !codeRef.current) {
      setOutput([{ content: "Pyodide is still loading...", error: true, frame: 0 }]);
      return false;
    }

    try {
      pyodide.FS.writeFile("curPattern.py", `from prelude import *
` + codeRef.current.getValue())
      pyodide.runPython(`import curPattern
import prelude
from tree import tree
import importlib
importlib.reload(curPattern)
`)
      return true;
    } catch (error: any) {
      setRunning(false)
      setOutput([{ content: error.toString(), error: true, frame: 0 }]);
      return false;
    }
  }

  //update the pattern in the filesystem
  function handleUpdate() {
    updatePattern();
  }

  function handleRun() {
    // stop running 
    if (running) {
      setRunning(false);
      return
    }

    // we want to start running
    if (updatePattern()) {
      setRunning(true)
      setOutput([])
    }
  }

  // if we see running change
  useEffect(() => {
    if (running) {
      if (pyodide == null) {
        return
      }
      const interval = setInterval(() => {
        const start = performance.now()
        try {
          const res = pyodide.runPython(`
curPattern.draw()
list(map(lambda x: [x.to_tuple()[0] / 255, x.to_tuple()[1] / 255, x.to_tuple()[2] / 255], tree.request_frame()))
`)
          setLights(res.toJs())
        } catch (error: any) {
          setRunning(false)
          appendOutput(error.toString(), 0)
        }
        const end = performance.now()
        setLoopTimes((prev) => {
          const newTimes = [...prev, end - start];
          return newTimes.slice(-20); // Keep only last 20 times
        })
      }, 22)

      return () => clearInterval(interval)
    }
  }, [running, pyodide])

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
            <span className="w-28 m-2">
              {loopTimes.length > 0
                ? (loopTimes.reduce((a, b) => a + b, 0) / loopTimes.length).toFixed(2)
                : "0.00"
              }ms / 22ms
            </span>
          </div>
          <div className="h-40 overflow-auto">{output.map((x, i) => (
            <div key={i} className={`flex px-2  ${i % 2 == 0 ? "bg-slate-100" : "bg-slate-200"}`}>
              <p className="font-mono flex-grow">
                {x.content}
              </p>
              <span className="text-slate-600 text-xs">frame {x.frame}</span>
            </div>


          ))}
            <div ref={bottomRef} />
          </div>
        </div>
      </div>
    </div >
  );
}
