"use client"

import { timeAgo } from "@/util/time";
import { Pattern } from "@prisma/client";
import Link from "next/link";

export default function PersonalPatterns({ patterns }: { patterns: Pick<Pattern, "id" | "title" | "modifiedAt">[] }) {

  return (

    <div className="text-black w-full bg-slate-200 h-80 rounded-4xl my-2 flex flex-col overflow-hidden p-4 gap-4">
      {patterns.map((x, i) => (
        <Link key={i} href={`/p/${x.id}`}>
          <div className="w-full bg-slate-300 rounded-xl p-4 flex">
            <span>{x.title}</span>
            <span className="flex-grow" />
            <span>{timeAgo(x.modifiedAt)}</span>

          </div>
        </Link>

      ))
      }
    </div >
  )

}
