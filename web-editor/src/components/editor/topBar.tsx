import { User } from "@/util/user";
import { Button } from "../ui/button";
import { createNew, savePattern } from "../landing/actions";
import { useEditor } from "@/util/context/editorContext";
import { useTransition } from "react";
import { useRouter } from "next/navigation";


export default function TopBar(user?: User) {
  const { codeRef, patternID } = useEditor()

  const [isPending, startTransition] = useTransition()

  const router = useRouter()
  if (typeof user !== undefined) {
    console.log("User provided");
  }

  const handleSave = () => {
    if (patternID) {
      startTransition(async () => {
        if (codeRef.current === null) return
        const res = await savePattern(patternID, codeRef.current.getValue())
      })
    } else {
      let name = window.prompt("Enter the pattern name")
      if (name !== null && name !== "") {
        createNew(name, codeRef.current?.getValue())
      }
    }
  }

  return (
    <div className="flex flex-row w-full justify-start py-4 gap-4 ps-4">
      <h2 onClick={() => router.push("/")}>GRIDmas</h2>
      <Button onClick={handleSave}>Save Now</Button>
    </div>
  )
}
