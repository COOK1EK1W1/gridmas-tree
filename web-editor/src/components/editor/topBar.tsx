import { Button } from "../ui/button";
import { createNew, savePattern } from "../landing/actions";
import { useEditor } from "@/util/context/editorContext";
import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check, CloudUpload, LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";


export default function TopBar({ user }: { user: any }) {
  const { codeRef, patternID, patternTitle, pattern, editorVal } = useEditor()

  const [lastSaved, setLastSaved] = useState(pattern)

  const [isPending, startTransition] = useTransition()

  const router = useRouter()

  const handleSave = () => {
    if (patternID) {
      startTransition(async () => {
        if (codeRef.current === null) return
        const res = await savePattern(patternID, codeRef.current.getValue())
        if (res.data) {
          setLastSaved(codeRef.current.getValue())
        }
      })
    } else {
      const name = window.prompt("Enter the pattern name")
      if (name !== null && name !== "") {
        startTransition(async () => {
          const res = await createNew(name, codeRef.current?.getValue())
          if (res.data) {
            router.push(`/p/${res.data.id}`)
          }
        })
      }
    }
  }
  console.log(user, "here")

  return (
    <div className="bg-gradient-to-r from-emerald-900 via-green-900 to-emerald-900 flex flex-row w-full h-15 p-2 flex justify-between items-center">
      <h2 onClick={() => router.push("/")} className="font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-red-500 via-yellow-300 to-green-500 text-xl cursor-pointer">GRIDmas Tree</h2>
      <div className="flex items-center">
        <div className="inline text-white px-2 font-semibold">{patternTitle}</div>
        {user ? (
          <Button onClick={handleSave} variant="green">
            <LoaderCircle className={cn('animate-spin', isPending ? "inline" : "hidden")} />
            <Check className={lastSaved === editorVal && !isPending ? "inline" : "hidden"} />
            <CloudUpload className={lastSaved !== editorVal && !isPending ? "inline" : "hidden"} />
            <span>Save Now</span>
          </Button>
        ) : (
          <Link href="/" className="text-white text-sm">
            <div className="text-right">Changes will not be saved </div>
            <div className="text-right">Sign in to save</div>
          </Link>
        )}
      </div>
    </div>
  )
}
