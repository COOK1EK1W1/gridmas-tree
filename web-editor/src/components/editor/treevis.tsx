import { useEditor } from "@/util/context/editorContext";
import { tree } from "@/util/trees/2025";
import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";

export default function TreeVis() {
  const { lights } = useEditor()
  return (
    <div className="h-[50dvh] bg-black">
      <Canvas>
        <ambientLight />
        {tree.map(([x, y, z], i) => (
          <mesh key={i} position={[x, z - 1, y]}>
            <sphereGeometry args={[0.025]} />
            <meshStandardMaterial color={lights[i] ? [lights[i][0], lights[i][1], lights[i][2]] : [0, 0, 0]} />
          </mesh>
        ))}
        <OrbitControls maxPolarAngle={1.3} enablePan={false} />
      </Canvas>

    </div>
  )

}
