"use client"
import { tree } from "@/util/trees/2025";
import { Billboard, Line, OrbitControls, Text } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Camera } from "lucide-react";
import { useEffect, useMemo, useRef, createRef } from "react";
import { Button } from "../ui/button";
import type { MeshStandardMaterial } from "three";

const treeHeight = Math.max(...tree.map((x) => x[2]))
export default function TreeVis({
  pyodide,
  running,
  onFrameMs,
  onLog,
}: {
  pyodide: any,
  running: boolean,
  onFrameMs?: (ms: number) => void,
  onLog?: (message: string, frame: number, isError?: boolean) => void,
}) {

  const canvasRef = useRef<any>(null)
  const frameRef = useRef<number>(0)

  // Create stable refs for each material without calling hooks in a loop
  const matRefs = useMemo(() => (
    Array.from({ length: tree.length }, () => createRef<MeshStandardMaterial>())
  ), [])

  function handlePhoto() {
    if (canvasRef.current === null) { return }

    const dataURL = canvasRef.current.domElement.toDataURL("image/jpeg")

    const image = new Image()
    image.src = dataURL
    image.onload = () => {
      const newCanvas = document.createElement("canvas")
      newCanvas.width = 420
      newCanvas.height = 750
      const ctx = newCanvas.getContext("2d")
      if (!ctx) return
      const startX = (image.width - 420) / 2;
      const startY = (image.height - 750) / 2;
      ctx.drawImage(image, startX, startY, 420, 750, 0, 0, 420, 750);

      // Save cropped image
      const croppedURL = newCanvas.toDataURL("image/jpeg");
      const link = document.createElement("a");
      link.download = "canvas-image.jpeg";
      link.href = croppedURL;
      document.body.appendChild(link)
      link.click();
      document.body.removeChild(link)
    }

  }


  // if we see running change
  useEffect(() => {
    if (running) {
      if (pyodide == null) {
        return
      }
      frameRef.current = 0
      const interval = setInterval(() => {
        const start = performance.now()
        try {
          const res: any = pyodide.runPython(`
curPattern.draw()
list(map(lambda x: [x.to_tuple()[0] / 255, x.to_tuple()[1] / 255, x.to_tuple()[2] / 255], tree.request_frame()))
`)
          const lights: number[][] = res.toJs()
          for (let i = 0; i < tree.length; i++) {
            const mat = matRefs[i].current
            if (mat) {
              // use setRGB for clarity
              mat.color.setRGB(lights[i][0], lights[i][1], lights[i][2])
            }
          }
          // prevent PyProxy leaks on older pyodide versions
          if (typeof res?.destroy === 'function') {
            res.destroy()
          }
        } catch (error: any) {
          // surface errors to the parent output panel
          onLog?.(String(error), frameRef.current, true)
        } finally {
          const end = performance.now()
          onFrameMs?.(end - start)
          frameRef.current += 1
        }
      }, 22)

      return () => clearInterval(interval)
    }
  }, [running, pyodide, matRefs, onFrameMs, onLog])


  return (
    <div className={`h-full `}>
      <div className="fixed bottom-2 right-2 hidden">
        <Button onClick={handlePhoto} className="cursor-pointer z-1000">
          <Camera />
        </Button>
      </div>


      {/* tree visualiser */}
      <Canvas style={{ background: "rgb(1, 1, 1)" }} gl={{ preserveDrawingBuffer: true }} onCreated={({ gl }) => {
        canvasRef.current = gl
      }} camera={{ translateY: 2 }}>
        <ambientLight />
        {tree.map(([x, y, z], i) => (
          <mesh key={i} position={[x, z, y]}>
            <sphereGeometry args={[0.025]} />
            <meshStandardMaterial ref={matRefs[i]} color={[0, 0, 0]} />
          </mesh>
        ))}
        {/*  X axis  */}
        <Line points={[[-1, 0, 0], [1, 0, 0]]} color={"red"} />
        <Billboard position={[1.2, 0, 0]}>
          <Text fontSize={0.3} color="red">
            X+
          </Text>
        </Billboard>
        <Billboard position={[-1.2, 0, 0]}>
          <Text fontSize={0.3} color="red">
            -X
          </Text>
        </Billboard>

        {/*  Y axis  */}
        <Line points={[[0, 0, -1], [0, 0, 1]]} color={"green"} />
        <Billboard position={[0, 0, 1.2]}>
          <Text fontSize={0.3} color="green">
            Y+
          </Text>
        </Billboard>
        <Billboard position={[0, 0, -1.2]}>
          <Text fontSize={0.3} color="green">
            -Y
          </Text>
        </Billboard>

        {/*  Z axis  */}
        <Line points={[[0, 0, 0], [0, treeHeight, 0]]} color={"blue"} />
        <Billboard position={[0, treeHeight + 0.2, 0]}>
          <Text fontSize={0.3} color="blue">
            Z+
          </Text>
        </Billboard>

        <OrbitControls maxPolarAngle={Math.PI - 1} enablePan={false} target={[0, treeHeight / 2, 0]} />
      </Canvas>

    </div >
  )

}
