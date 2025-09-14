import prisma from "@/util/prisma";
import { Pattern } from "@prisma/client";
import Login from "./signin";
import PersonalPattern from "./personalItems";

export default async function PersonalPatterns({ userData, patterns }: { userData: any, patterns: Pick<Pattern, "id" | "title" | "modifiedAt">[] }) {


  // if user exists, then grab their personal projects
  if (userData !== null) {

    const user = await prisma.user.findFirst({
      where: {
        email: userData.user.email
      },
      include: {
        patterns: true
      },
    })
    if (!user) {
      return <></>
    }
    patterns = user.patterns
  }

  if (userData === null) {
    return (
      <Login />
    )
  }

  if (patterns.length == 0) {
    return (
      <>
        <p className="text-black w-full">You have no patterns yet!</p>
        <Login />
      </>
    )
  }

  return (
    <div>
      <div className="text-black w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 p-4 gap-4">
        <PersonalPattern patterns={patterns} />
      </div>
    </div >
  )
}
