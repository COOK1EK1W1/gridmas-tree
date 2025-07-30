"use client"

import { Pattern } from "@prisma/client";
import Link from "next/link";

export default function PersonalPatterns({ patterns }: { patterns: Pick<Pattern, "id" | "title" | "modifiedAt">[] }) {

  return (

    <div className="text-black w-full bg-slate-200 h-80 rounded-4xl my-2 flex flex-wrap p-4 gap-4">
      {patterns.map((x, i) => (
        <Link key={i} href={`/p/${x.id}`}>
          <div className="bg-slate-300 h-20">
            <h4>{x.title}</h4>
          </div>
        </Link>

      ))
      }
    </div >
  )

}
