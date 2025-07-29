"use client"
import { useEditor } from "@/util/context/editorContext";
import { tree } from "@/util/trees/2025";
import { Billboard, Line, OrbitControls, Text } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { useState } from "react";

const treeHeight = Math.max(...tree.map((x) => x[2]))
const colors = ["bg-black", "bg-white", "bg-grey"]
export default function TreeVis() {
  const { lights } = useEditor()

  const [colorOpen, setColorOpen] = useState(false)
  const [bgColor, setBgColor] = useState<(typeof colors)[number]>("bg-black")

  return (
    <div className={`h-full ${bgColor}`}>
      {/* controls
      <div className="relative top-2 left-2">
        <div className={` h-10 bg-slate-500 duration-200 rounded-lg overflow-hidden ${colorOpen ? "w-30" : "w-10"}`} onMouseOver={() => setColorOpen(true)} onMouseOut={() => setColorOpen(false)} >
          <span className={`${bgColor} rounded-lg w-8 h-8 inline-block m-1`} onMouseDown={(a) => { setColorOpen(!a) }} />
          {colors.map((x, i) => (
            <span key={i} className={`${x} rounded-lg w-8 h-8 inline-block m-1`} onMouseDown={() => setBgColor(x)} />
          ))}
        </div>
      </div>
      */}


      {/* tree visualiser */}
      <Canvas camera={{ translateY: 2 }}>
        <ambientLight />
        {tree.map(([x, y, z], i) => (
          <mesh key={i} position={[x, z, y]}>
            <sphereGeometry args={[0.025]} />
            <meshStandardMaterial color={lights[i] ? [lights[i][0], lights[i][1], lights[i][2]] : [0, 0, 0]} />
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

    </div>
  )

}
