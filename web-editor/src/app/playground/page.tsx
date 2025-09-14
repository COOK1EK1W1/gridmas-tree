import PatternEditor from "@/components/editor/editor";
import EditorProvider from "@/util/context/editorProvider";
import { auth } from "@/util/auth";
import prisma from "@/util/prisma";
import { Pattern } from "@prisma/client";
import { headers } from "next/headers";

export default async function Mission() {
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

    //console.log(user);
  }
  // just use the offline provider
  return (
    <EditorProvider>
      <PatternEditor userData={userData} />
    </EditorProvider>
  )
}
