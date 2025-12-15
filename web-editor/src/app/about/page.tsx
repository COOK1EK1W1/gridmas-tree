import { Button } from "@/components/ui/button";
import Link from "next/link";

function FestiveLights({ position = "top" }: { position?: "top" | "bottom" }) {
  const bulbColors = ["#ef4444", "#22c55e", "#f59e0b", "#60a5fa", "#e879f9"]; // red, green, amber, blue, pink
  const bulbs = Array.from({ length: 40 });

  return (
    <div className="pointer-events-none relative w-full" aria-hidden>
      <div className={`absolute inset-x-0 w-full overflow-hidden ${position === "top" ? "-top-2" : "-bottom-2"} flex justify-center`}>
        <div className="flex items-center justify-center gap-2">
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

export default function About() {
  return (
    <div className="overflow-auto h-full bg-gradient-to-b from-emerald-900 via-green-900 to-emerald-950 text-orange-100 w-full flex flex-col items-center">
      {/* Background festive glows */}
      <div aria-hidden className="pointer-events-none absolute -top-24 left-1/2 -translate-x-1/2 h-64 w-64 rounded-full bg-red-500/20 blur-3xl" />
      <div aria-hidden className="pointer-events-none absolute bottom-10 right-10 h-64 w-64 rounded-full bg-emerald-500/20 blur-3xl" />

      <div className="w-full text-center py-8">
        <span className="text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-red-500 via-yellow-300 to-green-500 drop-shadow-[0_0_20px_rgba(234,179,8,0.15)]">
          About the GRIDmas Tree
        </span>
        <h2 className="text-2xl mt-2">A welcoming guide for curious humans</h2>
      </div>

      <FestiveLights position="top" />

      <div className="candy-frame rounded-4xl my-6 max-w-4xl space-y-5 p-6 text-left leading-relaxed text-black">
        <p>
          The GRIDmas Tree is a fully programmable Christmas tree with 1,000 RGB LEDs. Every light has a 3D coordinate, so we can paint patterns and animations that wrap around the whole tree in three-dimensional space.
        </p>
        <p>
          The idea started with Standup Maths&apos; 500-LED tree—his video is a great watch—and grew into something bigger: a tree with an easy-to-use API and web editor. Now anyone can design and test patterns without needing to be an expert coder.
        </p>
        <p>
          Created by Ciaran Cook in 2023, the tree became a friendly competition at Heriot-Watt University in 2024. This year a new API, better tools, and clear docs make it even easier to join in. Documentation is a team effort from Ciaran and Owen so you have everything you need in one place.
        </p>
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-2xl bg-emerald-950/40 p-4 border border-emerald-700/60">
            <h3 className="text-xl font-semibold mb-2">If you just like lights</h3>
            <p>
              You don&apos;t need to know code. Think of the tree as a canvas of tiny bulbs you can color and animate. Explore patterns, tweak colors, and see the tree react in real time.
            </p>
          </div>
          <div className="rounded-2xl bg-emerald-950/40 p-4 border border-emerald-700/60">
            <h3 className="text-xl font-semibold mb-2">If you&apos;re a student</h3>
            <p>
              Ready to join the competition? Start with the docs, try the web editor, and experiment in the playground. You can build patterns in Python, preview them, and submit them for your chance to win a prize.
            </p>
          </div>
        </div>
        <p>
          Whether you&apos;re here for the glow or to push the tech further, we&apos;re excited to see what you build. Dive into the resources below to start creating.
        </p>
      </div>

      <div className="flex gap-2 pb-10">
        <Link href="/">
          <Button variant="red">Back Home</Button>
        </Link>
        <Link href="/playground">
          <Button variant="green">Try the Playground</Button>
        </Link>
        <Link target="_blank" href="https://owen7000.github.io/gridmas-tree/">
          <Button variant="secondary">Read the Docs</Button>
        </Link>
      </div>

      <FestiveLights position="bottom" />
    </div>
  );
}
