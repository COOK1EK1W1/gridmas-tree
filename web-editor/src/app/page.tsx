import PersonalPatterns from "@/components/landing/personalProjects";
import Snow from "@/components/landing/snowLayer";
import { Button } from "@/components/ui/button";
import { auth } from "@/util/auth";
import prisma from "@/util/prisma";
import { Pattern } from "@prisma/client";
import { headers } from "next/headers";
import Image from "next/image";
import Link from "next/link";


function Example({ title, image, link }: { title: string, image: string, link: string }) {
  return (
    <Link href={link}>
      <div className="bg-slate-300 rounded-xl overflow-hidden" >
        <Image width={140} height={250} src={image} alt="3dplasma tree" />
        <h4 className="text-center">{title}</h4>
      </div >
    </Link >
  )

}

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
    <div className="overflow-auto h-[100dvh] bg-green-800 text-orange-100 w-full h-full flex flex-col items-center">
      <Snow />
      <div className="w-full text-center py-8">
        <h1 className="text-6xl font-bold">GRIDmas Tree</h1>
        <h2 className="text-2xl">Program GRID&apos;s Tree</h2>
      </div>

      <div className="flex gap-2 py-8">
        <Link href="/playground">
          <Button>Playground</Button>
        </Link>
        <Link href="/reference">
          <Button>Reference</Button>
        </Link>
      </div>

      <div className="w-8/9 md:w-125 lg:w-200">
        <h3> Example Patterns</h3>
        <div className="text-black w-full bg-slate-200 rounded-4xl my-2 flex flex-wrap p-4 gap-4">

          <Example title="3D Plasma" image="/3dplasma.jpeg" link="/p/3dplasma" />
          <Example title="3D Fire" image="/3dfire.jpeg" link="/p/3dfire" />
          <Example title="Caduceus" image="/caduceus.jpeg" link="/p/caduceus" />
          <Example title="Borealis" image="/borealis.jpeg" link="/p/borealis" />
          <Example title="Wave Flow" image="/waveflow.jpeg" link="/p/waveflow" />

        </div>
      </div>


      <div className="w-8/9 md:w-125 lg:w-200">
        <h3> Your Patterns</h3>
        <PersonalPatterns patterns={patterns} />
      </div>

    </div >
  )
}
