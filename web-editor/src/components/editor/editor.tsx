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
  const { codeRef } = useEditor()
  const { pyodide, loading } = usePyodide();

  const [output, setOutput] = useState<Message[]>([]);
  const [running, setRunning] = useState(false);
  const [loopTimes, setLoopTimes] = useState<number[]>([])
  const [libsReady, setLibsReady] = useState(false)
  const bottomRef = useRef<HTMLDivElement | null>(null);

  function appendOutput(x: string, frame: number, isError = false) {
    setOutput((prev) => {
      const a = [...prev, { content: x, frame: frame, error: isError }]
      // keep console to last 200 lines for smooth scrolling
      if (a.length > 400) {
        return a.slice(-200)
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
      pyodide.globals.set("print_to_react", (s: string, frame: number) => appendOutput(s, frame));

      // load all the core libraries
      const files = ["util.py", "colors.py", "tree.csv", "prelude.py", "tree.py", "particle_system.py"]
      const base = process.env.NEXT_PUBLIC_BASEURL ?? ""
      Promise.all(files.map(async (x) => {
        const res = await fetch(`${base}/api/send-script?s=${x}`)
        if (!res.ok) throw new Error(`Failed to fetch ${x}: ${res.status}`)
        const res2 = await res.text()
        pyodide.FS.writeFile(x, res2)
      })).then(() => {
        // redirect stdout/stderr after libs are in place
        pyodide.runPython(`import sys

class JSWriter:
    def write(self, s):
        if s.strip():
            print_to_react(s, 0)

    def flush(self):
        pass

sys.stdout = JSWriter()
sys.stderr = JSWriter()`)
        // initialize the tree so that tree.pixels etc. are available
        pyodide.runPython(`from tree import tree\ntree.init("tree.csv")`)
        setLibsReady(true)
      }).catch((e: any) => {
        setLibsReady(false)
        appendOutput(`Failed to load core libraries: ${e?.message ?? String(e)}`, 0, true)
      })
    }
  }, [pyodide, loading]);

  // Helper function to update the pattern
  function updatePattern() {
    if (!pyodide || !codeRef.current) {
      setOutput([{ content: "Pyodide is still loading...", error: true, frame: 0 }]);
      return false;
    }
    if (!libsReady) {
      appendOutput("Runtime is initializing libraries...", 0, true)
      return false
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
      setLoopTimes([])
    }
  }

  const avgMs = loopTimes.length > 0
    ? (loopTimes.reduce((a, b) => a + b, 0) / loopTimes.length)
    : 0
  const fps = avgMs > 0 ? (1000 / avgMs) : 0

  const isReady = !!pyodide && libsReady && !loading

  return (
    <div className="h-full flex flex-row">
      <div className="w-1/2 bg-slate-200 h-full">
        <TopBar />
        <CodeEditor />
      </div>
      <div className="w-1/2 h-screen flex flex-col">
        <div className="flex-grow">
          <TreeVis
            pyodide={pyodide}
            running={running}
            onFrameMs={(ms) => setLoopTimes((prev) => [...prev.slice(-199), ms])}
            onLog={(message, frame, isError) => appendOutput(message, frame, isError)}
          />
        </div>
        <div className="h-52">
          <div className="h-12 flex items-center">
            <Button className="w-28 m-2" onClick={handleRun} disabled={!isReady}>
              {!running ? (isReady ? "Run" : "Loading…") : "Stop"}
            </Button>
            <Button className="w-28 m-2" onClick={handleUpdate} disabled={!isReady}>Update</Button>
            <span className="w-28 m-2">
              {avgMs.toFixed(2)}ms ({fps.toFixed(1)} fps) / 22ms
            </span>
          </div>
          <div className="h-40 overflow-auto">
            {output.map((x, i) => (
              <div key={i} className={`flex px-2  ${i % 2 == 0 ? "bg-slate-100" : "bg-slate-200"}`}>
                <p className={`font-mono flex-grow ${x.error ? "text-red-600" : ""}`}>
                  {x.content}
                </p>
                {x.frame !== 0 && (
                  <span className="text-slate-600 text-xs">frame {x.frame}</span>
                )}
              </div>


            ))}
            <div ref={bottomRef} />
          </div>
        </div>
      </div>
    </div >
  );
}
