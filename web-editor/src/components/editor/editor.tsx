"use client"
import CodeEditor from "./code";
import TreeVis from "./treevis";
import { useEffect, useRef, useState } from "react";
import { useEditor } from "@/util/context/editorContext";
import TopBar from "./topBar";
import { Button } from "../ui/button";
import { usePyodide } from "@/util/usePyodide";
import JSZip from "jszip";
import Attributes from "./attributes";

// Global variable to store preloaded zip data
declare global {
  var preloadedZipData: Blob | null;
}

type Message = {
  content: string,
  error: boolean,
  frame: number
}

export default function PatternEditor({ userData }: { userData: any }) {
  const { codeRef } = useEditor()
  const { pyodide, loading } = usePyodide();

  const [output, setOutput] = useState<Message[]>([]);
  const [running, setRunning] = useState(false);
  const [libsReady, setLibsReady] = useState(false)
  const [zipPreloaded, setZipPreloaded] = useState(false)
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Preload the zip file as soon as the component mounts
  useEffect(() => {
    const preloadZip = async () => {
      if (globalThis.preloadedZipData) {
        setZipPreloaded(true)
        return
      }

      try {
        const base = process.env.NEXT_PUBLIC_BASEURL ?? ""
        const res = await fetch(`${base}/api/send-scripts-zip`)
        if (res.ok) {
          globalThis.preloadedZipData = await res.blob()
          setZipPreloaded(true)
        }
      } catch (error) {
        console.warn('Failed to preload zip data:', error)
        // Don't set zipPreloaded to true, so we'll try again later
      }
    }

    preloadZip()
  }, [])


  // add a message to the output section, used as a hook from inside pyodide
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




  // Scrolls to the bottom every time messages change
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [output]);




  // Initialize Pyodide when it's loaded
  useEffect(() => {
    if (pyodide && !loading) {
      pyodide.globals.set("print_to_react", (s: string, frame: number) => appendOutput(s, frame));

      const loadCoreLibraries = async () => {
        try {
          let zipBlob: Blob

          // Use preloaded data if available, otherwise fetch it
          if (globalThis.preloadedZipData) {
            zipBlob = globalThis.preloadedZipData
          } else {
            // Fallback: fetch the zip file if preloading failed
            const base = process.env.NEXT_PUBLIC_BASEURL ?? ""
            const res = await fetch(`${base}/api/send-scripts-zip`)
            if (!res.ok) throw new Error(`Failed to fetch core libraries zip: ${res.status}`)
            zipBlob = await res.blob()
          }

          const zip = new JSZip()
          const zipContents = await zip.loadAsync(zipBlob)

          // Extract and write each file to Pyodide's filesystem
          const filePromises = Object.keys(zipContents.files).map(async (fileName) => {
            const file = zipContents.files[fileName]
            if (!file.dir) { // Skip directories
              const content = await file.async('text')
              pyodide.FS.writeFile(fileName, content)
            }
          })

          await Promise.all(filePromises)

          // setup redirect stdout/stderr after libs are in place
          pyodide.runPython(`
import sys

class JSWriter:
    def write(self, s):
        if s.strip():
            print_to_react(s, 0)

    def flush(self):
        pass

sys.stdout = JSWriter()
sys.stderr = JSWriter()`)

          // initialize the tree so that pixels() etc. are available
          pyodide.runPython(`
from gridmas import *
Store.instance = None
tree.init("tree.csv")
`)
          setLibsReady(true)

        } catch (e: any) {
          setLibsReady(false)
          appendOutput(`Failed to load core libraries: ${e?.message ?? String(e)}`, 0, true)
        }
      }

      loadCoreLibraries()
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
      pyodide.FS.writeFile("curPattern.py", codeRef.current.getValue())
      pyodide.runPython(`import curPattern
import importlib
Store.instance = None
importlib.reload(curPattern)
tree._pattern_reset()
`)
      // Reset the generator when pattern is updated
      pyodide.runPython(`
if 'pattern_generator' in globals():
    pattern_generator = None
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
      // Reset the generator when stopping
      if (pyodide) {
        pyodide.runPython(`
if 'pattern_generator' in globals():
    pattern_generator = None
`)
      }
      return
    }

    // we want to start running
    if (updatePattern()) {
      setRunning(true)
      setOutput([])
      // Reset the generator when starting
      if (pyodide) {
        pyodide.runPython(`
if 'pattern_generator' in globals():
    pattern_generator = None
`)
      }
    }
  }

  const isReady = !!pyodide && libsReady && !loading && zipPreloaded

  return (
    <div className="fixed h-full w-full flex flex-col">
      <div className="w-full flex md:flex-row flex-col flex-grow">
        <div className="flex flex-col md:w-1/2">
          <TopBar user={userData} />
          <CodeEditor />
        </div>
        <TreeVis
          pyodide={pyodide}
          running={running}
          onLog={(message, frame, isError) => appendOutput(message, frame, isError)}
        />
      </div>
      <div className="h-52 flex flex-col-reverse md:flex-row">
        <Attributes />
        <div className="md:w-1/2">
          <div className="h-12 flex items-center">
            <Button className="w-28 m-2" onClick={handleRun} variant="red" disabled={!isReady}>
              {!running ? (isReady ? "Run" : (zipPreloaded ? "Loading…" : "Preloading…")) : "Stop"}
            </Button>

            <div className="block md:hidden text-white text-sm">
              To edit code, please open the editor on a desktop or laptop device.
            </div>
          </div>
          <div className="h-40 overflow-auto hidden md:block">
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
