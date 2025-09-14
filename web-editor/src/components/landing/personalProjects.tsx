"use client"

import { timeAgo } from "@/util/time";
import { Pattern } from "@prisma/client";
import Link from "next/link";
import { CirclePlus, Dot, MoreVertical } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { createNew } from "./actions";
import Login from "./signin";
import { signOut } from "@/util/auth-client";

export default function PersonalPatterns({ userData, patterns }: { userData: any, patterns: Pick<Pattern, "id" | "title" | "modifiedAt">[] }) {
  const onAction = (action: string, id: string) => {
    // Stub implementations
    console.log(`${action} clicked for`, id)
  }

  if (userData === null) {
    return (
      <div className="candy-frame rounded-4xl my-2">
        <Login />
      </div>
    )
  }

  if (patterns.length == 0) {
    return (
      <div className="candy-frame rounded-4xl my-2">
        <p className="text-black w-full">You have no patterns yet!</p>
        <Login />
      </div>
    )
  }

  const handleCreateNew = () => {
    let name = window.prompt("Enter the pattern name")
    if (name !== null && name !== "") {
      createNew(name)
    }
  }

  return (
    <div>
      <div className="flex justify-between">
        <span className="font-semibold tracking-wide">🎄 Your Patterns</span>
        {userData ? <span className="flex font-semibold"> {userData.user.email} <Dot /> <span onClick={() => signOut()}>Sign Out</span></span> : null}
      </div>
      <div className="candy-frame rounded-4xl my-2">
        <div className="text-black w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 p-4 gap-4">
          {patterns.map((pattern) => (
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
                  <DropdownMenuItem onSelect={() => onAction("Rename", pattern.id)}>Rename</DropdownMenuItem>
                  <DropdownMenuItem onSelect={() => onAction("Duplicate", pattern.id)}>Duplicate</DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem className="text-red-700" onSelect={() => onAction("Delete", pattern.id)}>Delete</DropdownMenuItem>
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

          <div className="relative w-[210px]" onClick={handleCreateNew}>
            <div className="w-full h-20 rounded-xl overflow-hidden border border-red-200/40 bg-gradient-to-b from-white to-red-50/60 shadow-[0_10px_30px_-10px_rgba(220,38,38,0.35)] hover:shadow-[0_12px_40px_-8px_rgba(220,38,38,0.55)] transition">
              <div className="h-full p-2 text-red-800 flex flex-col items-center justify-around">
                <CirclePlus />
                <h4 className="text-center font-semibold text-sm leading-tight">New pattern</h4>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div >
  )
}
