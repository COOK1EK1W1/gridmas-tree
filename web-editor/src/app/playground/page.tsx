import PatternEditor from "@/components/editor/editor";
import EditorProvider from "@/util/context/editorProvider";

export default async function Mission() {
  // just use the offline provider
  return (
    <EditorProvider>
      <PatternEditor />
    </EditorProvider>
  )
}
