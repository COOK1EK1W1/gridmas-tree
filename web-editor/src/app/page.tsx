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

  // Load Pyodide when the component mounts
  useEffect(() => {
    const loadPyodide = async () => {
      const pyodideInstance = await window.loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
      });
      setPyodide(pyodideInstance);
      ["util.py", "pixel_driver/pixel_driver.py", "colors.py", "tree.py"].map((x) => {
        fetch(`https://raw.githubusercontent.com/COOK1EK1W1/gridmas-tree/refs/heads/main/backend/${x}`).then((res) =>
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
    if (pyodide) {
      try {
        pyodide.runPythonAsync(editorRef.current.getValue())
        setOutput("running");
      } catch (error) {
        setOutput(error.toString());
      }
    } else {
      setOutput("Pyodide is still loading...");
    }
  }

  return (
    <div className="h-full flex flex-row">
      <div className="w-1/2 bg-slate-200 h-full">
        <Editor onMount={handleEditorDidMount} height="100vh" defaultLanguage="python" />
      </div>
      <div className="w-1/2 h-full">
        <div className="h-[50dvh] bg-black">
          <Canvas>
            <ambientLight />
            {tree.map(([x, y, z], i) => (
              <mesh key={i} position={[x, z - 1, y]}>
                <sphereGeometry args={[0.025]} />
                <meshStandardMaterial color="hotpink" />
              </mesh>
            ))}
            <OrbitControls maxPolarAngle={1.3} enablePan={false} />
          </Canvas>

        </div>
        <button onClick={handleRun}>run</button>
        <div>{output}</div>
      </div>
      <script src="https://cdn.jsdelivr.net/pyodide/v0.23.4/full/pyodide.js"></script>
    </div >
  );
}
