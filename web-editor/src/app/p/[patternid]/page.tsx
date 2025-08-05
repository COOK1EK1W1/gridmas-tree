import PatternEditor from "@/components/editor/editor";
import { auth } from "@/util/auth";
import CloudEditorProvider from "@/util/context/cloudEditorProvider";
import prisma from "@/util/prisma";
import { tryCatch } from "@/util/try-catch";
import { headers } from "next/headers";
import NotFound from "./notfound";

export default async function Pattern({ params }: { params: Promise<{ patternid: string }> }) {
  const patternId = (await params).patternid

  // get the user data
  const userData = await auth.api.getSession({ headers: await headers() })

  // get the pattern data
  const patternData = await tryCatch(prisma.pattern.findUnique({ where: { id: patternId } }))
  if (patternData.error !== null || patternData.data === null) {
    console.log(patternData.error)
    return <NotFound />
  }

  // import the mission from the data

  return (
    <CloudEditorProvider cloudPattern={patternData.data}>
      <PatternEditor />
    </CloudEditorProvider>
  )
}
