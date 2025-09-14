import ExampleProjects from "@/components/landing/exampleProjects";
import PersonalPatterns from "@/components/landing/personalProjects";
import SignoutBit from "@/components/landing/signout";
import Snow from "@/components/landing/snowLayer";
import { Button } from "@/components/ui/button";
import { auth } from "@/util/auth";
import { Pattern } from "@prisma/client";
import { headers } from "next/headers";
import Link from "next/link";
import { Suspense } from "react";

function FestiveLights({ position = "top" }: { position?: "top" | "bottom" }) {
  const bulbColors = ["#ef4444", "#22c55e", "#f59e0b", "#60a5fa", "#e879f9"]; // red, green, amber, blue, pink
  const bulbs = Array.from({ length: 36 });
  return (
    <div className="pointer-events-none relative w-full" aria-hidden>
      <div className={`absolute inset-x-0 ${position === "top" ? "-top-2" : "-bottom-2"} flex justify-center`}>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {bulbs.map((_, i) => {
            const color = bulbColors[i % bulbColors.length];
            return (
              <span
                key={i}
                className="festive-bulb h-2 w-2 rounded-full"
                style={{ color, animationDelay: `${i * 0.08}s` }}
              />
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default async function Home() {
  const userData = await auth.api.getSession({ headers: await headers() })
  let patterns: Pick<Pattern, "title" | "modifiedAt" | "id">[] = [];

  return (
    <div className="overflow-auto h-full bg-gradient-to-b from-emerald-900 via-green-900 to-emerald-950 text-orange-100 w-full flex flex-col items-center">
      <Snow />

      {/* Background festive glows */}
      <div aria-hidden className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-64 w-64 rounded-full bg-red-500/20 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute bottom-10 right-10 h-64 w-64 rounded-full bg-emerald-500/20 blur-3xl" />

      <div className="w-full text-center py-8">
        <h1 className="text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-red-500 via-yellow-300 to-green-500 drop-shadow-[0_0_20px_rgba(234,179,8,0.15)]">
          GRIDmas Tree
        </h1>
        <h2 className="text-2xl mt-2">Program GRID&apos;s Tree ✨❄️</h2>
      </div>

      <FestiveLights position="top" />

      <div className="flex gap-2 py-8">
        <Link href="/playground">
          <Button className="bg-red-600 hover:bg-red-700 text-white border border-red-300/40 shadow-lg shadow-red-500/20 hover:shadow-red-500/40 transition-transform hover:-translate-y-0.5">Playground</Button>
        </Link>
        <Link href="/reference">
          <Button className="bg-emerald-600 hover:bg-emerald-700 text-white border border-emerald-300/40 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 transition-transform hover:-translate-y-0.5">Reference</Button>
        </Link>
      </div>

      <div>
        <div className="flex justify-between">
          <span className="font-semibold tracking-wide">🎄 Your Patterns</span>
          <SignoutBit userData={userData} />
        </div>
        <div className="candy-frame rounded-4xl my-2">
          <Suspense>
            <PersonalPatterns patterns={patterns} userData={userData} />
          </Suspense>
        </div>
      </div>

      <div>
        <h3 className="font-semibold tracking-wide">🎁 Example Patterns</h3>
        <div className="candy-frame rounded-4xl my-2">
          <ExampleProjects />
        </div>
      </div>

      <FestiveLights position="bottom" />
    </div >
  )
}
