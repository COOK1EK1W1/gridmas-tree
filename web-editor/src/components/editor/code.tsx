import { useEditor } from "@/util/context/editorContext";
import { Editor, OnMount } from "@monaco-editor/react";

export default function CodeEditor() {
  const { codeRef, pattern, setEditorVal } = useEditor()

  // let the global state manager know where we are
  const handleEditorDidMount: OnMount = (editor, monaco) => {
    codeRef.current = editor;
  }

  return (
    <div>
      {/* use default wave pattern if no cloud pattern */}
      <Editor onChange={(a) => setEditorVal(a ?? "")} onMount={handleEditorDidMount} height="100vh" defaultLanguage="python" defaultValue={pattern === "" ? `import time
import math
from gridmas import *

wave_offset = 0  # this will move the wave up along the z-axis (height)
wave_speed = 0.03
wave_period = 0.5
color_change_rate = 0.2

def draw():
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
        pixel.set(wave_intensity_color)

        # increase the wave offset to move the wave upwards
    wave_offset = (wave_offset + wave_speed) % (6)` : pattern} />
    </div >
  )
}
