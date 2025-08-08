"use client"
import { tree } from "@/util/trees/2025";
import { Billboard, Line, OrbitControls, Text } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Camera } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "../ui/button";

const treeHeight = Math.max(...tree.map((x) => x[2]))
export default function TreeVis({ pyodide, running }: { pyodide: any, running: boolean }) {

  const [lights, setLights] = useState<number[][]>([])
  const canvasRef = useRef<any>(null)
  const matRefs = []
  for (let i = 0; i < tree.length; i++) {
    matRefs.push(useRef(null))
  }

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
      const interval = setInterval(() => {
        const start = performance.now()
        try {
          const res: any = pyodide.runPython(`
curPattern.draw()
list(map(lambda x: [x.to_tuple()[0] / 255, x.to_tuple()[1] / 255, x.to_tuple()[2] / 255], tree.request_frame()))
`)
          const lights = res.toJs()
          for (let i = 0; i < tree.length; i++) {
            matRefs[i].current.color.r = lights[i][0]
            matRefs[i].current.color.g = lights[i][1]
            matRefs[i].current.color.b = lights[i][2]
            //matRefs[i].current.color = [lights[i][0] / 255, lights[i][1] / 255, lights[i][2] / 255]
          }
          // prevent PyProxy leaks on older pyodide versions
          if (typeof res?.destroy === 'function') {
            res.destroy()
          }
        } catch (error: any) {
          console.log(error)
        }
        const end = performance.now()
      }, 22)

      return () => clearInterval(interval)
    }
  }, [running, pyodide])


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
