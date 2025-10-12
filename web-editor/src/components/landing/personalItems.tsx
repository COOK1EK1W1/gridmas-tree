"use client"
import { CirclePlus } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { timeAgo } from "@/util/time";
import { MoreVertical } from "lucide-react";
import Link from "next/link";
import { createNew, deletePattern, duplicatePattern, renamePattern } from "./actions";
import { Pattern } from "@prisma/client";
import { useTransition } from "react";
import { useRouter } from "next/navigation";

export default function PersonalPattern({ patterns }: { patterns: Pick<Pattern, "title" | "modifiedAt" | "id">[] }) {
  const [isPending, startTransition] = useTransition()
  const router = useRouter()

  const handleCreateNew = () => {
    const name = window.prompt("Enter the pattern name")
    if (name !== null && name !== "") {
      startTransition(async () => {
        const a = await createNew(name)
        if (a.error === null) {
          router.push(`/p/${a.data.id}`)
        } else {
          window.alert("there was an issue creating the pattern")
        }
      })
    }
  }

  const handleDelete = (id: string) => {
    startTransition(async () => {
      const a = await deletePattern(id)
      if (a.error === null) {
        router.push("/")
      } else {
        window.alert("there was an issue creating the pattern")
      }
    })
  }

  const handleRename = (id: string) => {
    const name = window.prompt("Enter the new name")
    if (name !== null && name !== "") {
      startTransition(async () => {
        const a = await renamePattern(id, name)
        if (a.error === null) {
          router.push("/")
        } else {
          window.alert("there was an issue creating the pattern")
        }
      })
    }
  }


  const handleDuplicate = (id: string) => {
    const name = window.prompt("Enter the new name")
    if (name !== null && name !== "") {
      startTransition(async () => {
        const a = await duplicatePattern(id, name)
        if (a.error === null) {
          router.push("/")
        } else {
          window.alert("there was an issue creating the pattern")
        }
      })
    }
  }


  const onAction = (action: string, id: string) => {
    // Stub implementations
    console.log(`${action} clicked for`, id)
  }

  return (
    <>
      {patterns.sort((x, y) => y.modifiedAt.getTime() - x.modifiedAt.getTime()).map((pattern, i) => (
        <div key={pattern.id} className="relative w-[210px]">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                aria-label="Pattern options"
                className="absolute right-1 top-1 z-10 rounded-md p-1 text-red-800/70 hover:text-red-900 hover:bg-red-100/60"
              >
                <MoreVertical className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent sideOffset={8} align="end">
              <DropdownMenuItem onSelect={() => handleRename(pattern.id)}>Rename</DropdownMenuItem>
              <DropdownMenuItem onSelect={() => handleDuplicate(pattern.id)}>Duplicate</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-700" onSelect={() => handleDelete(pattern.id)}>Delete</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>

          <Link href={`/p/${pattern.id}`}>
            <div className="w-full h-20 rounded-xl overflow-hidden border border-red-200/40 bg-gradient-to-b from-white to-red-50/60 shadow-[0_10px_30px_-10px_rgba(220,38,38,0.35)] hover:shadow-[0_12px_40px_-8px_rgba(220,38,38,0.55)] transition">
              <div className="px-3 pt-7 pb-3">
                <h4 className="text-center text-red-800 font-semibold text-sm leading-tight">{pattern.title}</h4>
                <p className="text-center text-[11px] text-red-900/70 mt-1">{timeAgo(pattern.modifiedAt)}</p>
              </div>
            </div>
          </Link>
        </div>
      ))}

      < div className="relative w-[210px]" onClick={handleCreateNew} >
        <div className="w-full h-20 rounded-xl overflow-hidden border border-red-200/40 bg-gradient-to-b from-white to-red-50/60 shadow-[0_10px_30px_-10px_rgba(220,38,38,0.35)] hover:shadow-[0_12px_40px_-8px_rgba(220,38,38,0.55)] transition">
          <div className="h-full p-2 text-red-800 flex flex-col items-center justify-around">
            <CirclePlus className={isPending ? "animate-spin" : ""} />
            <h4 className="text-center font-semibold text-sm leading-tight">New Pattern</h4>
          </div>
        </div>
      </div >
    </>
  )
}
