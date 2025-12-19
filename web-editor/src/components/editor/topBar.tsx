import { Button } from "../ui/button";
import { createNew, savePattern } from "../landing/actions";
import { useEditor } from "@/util/context/editorContext";
import { useState, useTransition, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Check, CloudUpload, LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";


export default function TopBar({ user }: { user: any }) {
  const { codeRef, patternID, patternTitle, pattern, patternOwnerId } = useEditor()

  const [lastSaved, setLastSaved] = useState(pattern)
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  const [isPending, startTransition] = useTransition()

  const router = useRouter()

  // Update lastSaved when pattern prop changes
  useEffect(() => {
    setLastSaved(pattern)
    setHasUnsavedChanges(false)
  }, [pattern])

  // Timer to check for changes every second
  useEffect(() => {
    const interval = setInterval(() => {
      if (codeRef.current === null) return
      
      const currentValue = codeRef.current.getValue()
      const hasChanges = currentValue !== lastSaved
      setHasUnsavedChanges(hasChanges)
    }, 1000)

    return () => clearInterval(interval)
  }, [codeRef, lastSaved])

  const userId = user?.user?.id
  const ownsPattern = Boolean(userId && patternOwnerId && userId === patternOwnerId)
  const shouldAutoSave = Boolean(ownsPattern && patternID)

  const handleSave = useCallback(() => {
    console.log("saving")
    if (patternID) {
      startTransition(async () => {
        if (codeRef.current === null) return
        const res = await savePattern(patternID, codeRef.current.getValue())
        if (res.data) {
          const savedValue = codeRef.current.getValue()
          setLastSaved(savedValue)
          setHasUnsavedChanges(false)
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
  }, [codeRef, patternID, router, startTransition])

  // Autosave every 10s when user owns the pattern and there are unsaved changes
  useEffect(() => {
    if (!shouldAutoSave) return

    const interval = setInterval(() => {
      if (!hasUnsavedChanges || isPending) return
      handleSave()
    }, 5_000)

    return () => clearInterval(interval)
  }, [handleSave, hasUnsavedChanges, isPending, shouldAutoSave])

  return (
    <div className="bg-gradient-to-r from-emerald-900 via-green-900 to-emerald-900 flex flex-row w-full h-15 p-2 flex justify-between items-center">
      <h2 onClick={() => router.push("/")} className="font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-red-500 via-yellow-300 to-green-500 text-xl cursor-pointer">GRIDmas Tree</h2>
      <div className="flex items-center">
        <div className="inline text-white px-2 font-semibold">{patternTitle}</div>
        {user ? (
          <Button onClick={handleSave} variant="green">
            <LoaderCircle className={cn('animate-spin', isPending ? "inline" : "hidden")} />
            <Check className={!hasUnsavedChanges && !isPending ? "inline" : "hidden"} />
            <CloudUpload className={hasUnsavedChanges && !isPending ? "inline" : "hidden"} />
            <span>Save Now</span>
          </Button>
        ) : (
          <Link href="/" className="text-white text-sm pl-2">
            <div className="text-right">Sign in to</div>
            <div className="text-right">save changes </div>
          </Link>
        )}
      </div>
    </div>
  )
}
