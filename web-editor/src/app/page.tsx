import PersonalPatterns from "@/components/landing/personalProjects";
import Snow from "@/components/landing/snowLayer";
import { auth } from "@/util/auth";
import prisma from "@/util/prisma";
import { Pattern } from "@prisma/client";
import { headers } from "next/headers";
import Link from "next/link";

export default async function Home() {
  const userData = await auth.api.getSession({ headers: await headers() })
  let patterns: Pick<Pattern, "title" | "modifiedAt" | "id">[] = [];

  // if user exists, then grab their personal projects
  if (userData !== null) {

    const user = await prisma.user.findFirst({
      where: {
        email: userData.user.email
      },
      include: {
        patterns: {
          select: {
            title: true,
            modifiedAt: true,
            id: true,
          },
          orderBy: {
            modifiedAt: "desc"
          }
        }
      },
    })
    if (!user) {
      return <></>
    }
    patterns = user.patterns
  }

  return (
    <div className="bg-green-800 text-orange-100 w-full h-full flex flex-col items-center">
      <Snow />
      <div className="w-full text-center py-16">
        <h1 className="text-8xl font-bold">GRIDmas Tree</h1>
        <h2 className="text-2xl">Program GRID&apos;s Tree</h2>
      </div>

      <Link href="/playground" className="p-2 bg-slate-200 text-black rounded-xl">Playground</Link>

      <div className="w-1/2">
        <h3> Example Patterns</h3>
        <div className="text-black w-full bg-slate-200 h-80 rounded-4xl my-2 flex flex-wrap p-4 gap-4">

          <div className="bg-slate-300 h-20">
            <h4>Wave Flow</h4>
          </div>

          <div className="bg-slate-300 h-20">
            <h4>3d Fire</h4>
          </div>

          <div className="bg-slate-300 h-20">
            <h4>Jumpy Balls</h4>
          </div>

        </div>
      </div>


      <div className="w-1/2">
        <h3> Your Patterns</h3>
        <PersonalPatterns patterns={patterns} />
      </div>

    </div >
  )
}
