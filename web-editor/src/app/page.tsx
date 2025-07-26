"use client"
import { Editor } from "@monaco-editor/react";
import { useEffect, useRef, useState } from "react";
import { PyodideInterface } from "pyodide";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { tree } from "./tree"

export default function Home() {
  const editorRef = useRef<any>(null)

  const [pyodide, setPyodide] = useState<PyodideInterface | null>(null);
  const [output, setOutput] = useState("");
  const [lights, setLights] = useState<Array<Array<number>>>([]);
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
        fetch(`http://localhost:3000/api/send-script?s=${x}`).then((res) =>
          res.text().then(res2 => {
            console.log(res2)
            pyodideInstance.FS.writeFile(x, res2)
          })
        )
      })
    };

    loadPyodide();
  }, []);


  function handleEditorDidMount(editor, monaco) {
    editorRef.current = editor;
  }

  function handleRun() {
    // stop running 
    if (running) {
      setRunning(false);
      return
    }

    // we want to start running
    if (pyodide) {
      try {
        pyodide.FS.writeFile("curPattern.py", `from prelude import *
` + editorRef.current.getValue())
        pyodide.runPython(`import curPattern
import prelude
from tree import tree
import importlib
importlib.reload(curPattern)
`)
        setRunning(true)
        setOutput("")
      } catch (error) {
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
        } catch (error) {
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
        <Editor onMount={handleEditorDidMount} height="100vh" defaultLanguage="python" defaultValue={`

import time
import math

wave_offset = 0  # this will move the wave up along the z-axis (height)

def draw():
    wave_speed = 0.03
    wave_period = 0.5
    color_change_rate = 0.2
    global wave_offset

    # slowly change color over time for the wave (rainbow-like cycle)
    r = int((math.sin(color_change_rate * time.time()) + 1) / 2 * 255)
    g = int((math.sin(color_change_rate * time.time() + 2 * math.pi / 3) + 1) / 2 * 255)
    b = int((math.sin(color_change_rate * time.time() + 4 * math.pi / 3) + 1) / 2 * 255)
    wave_color = (r, g, b)

    for pixel in tree.pixels:
        # a basic 3d wave function based on the z-coordinate and a changing 'wave_offset'
        intensity = 0.5 * (math.cos(2 * math.pi * (pixel.z / tree.height + wave_offset) / wave_period) + 1)
        # using intensity to modify the brightness of the color
        wave_intensity_color = Color(int(wave_color[0] * intensity), int(wave_color[1] * intensity), int(wave_color[2] * intensity))

        # set the light to the calculated color
        pixel.set_color(wave_intensity_color)

        # increase the wave offset to move the wave upwards
        wave_offset = (wave_offset + wave_speed) % (6)`} />
      </div>
      <div className="w-1/2 h-full">
        <div className="h-[50dvh] bg-black">
          <Canvas>
            <ambientLight />
            {tree.map(([x, y, z], i) => (
              <mesh key={i} position={[x, z - 1, y]}>
                <sphereGeometry args={[0.025]} />
                <meshStandardMaterial color={lights[i] ?? 0} />
              </mesh>
            ))}
            <OrbitControls maxPolarAngle={1.3} enablePan={false} />
          </Canvas>

        </div>
        <button onClick={handleRun} className={`cursor-pointer bg-slate-800 w-28 py-1 rounded-xl m-2 ${running ? "bg-green" : ""}`}>{!running ? "run" : "stop"}</button>
        <p>{(loopTimes.reduce((a, b) => a + b, 0) / loopTimes.length).toFixed(2)}ms / 22ms</p>
        <div>{output}</div>
      </div>
      <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
    </div >
  );
}
