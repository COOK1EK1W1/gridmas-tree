import PatternEditor from "@/components/editor/editor";
import { auth } from "@/util/auth";
import CloudEditorProvider from "@/util/context/cloudEditorProvider";
import prisma from "@/util/prisma";
import { headers } from "next/headers";

export default async function Pattern({ params }: { params: Promise<{ patternid: string }> }) {
  const patternId = (await params).patternid

  // get the user data
  let userData = await auth.api.getSession({ headers: await headers() })

  // get the pattern data
  const patternData = await prisma.pattern.findUnique({ where: { id: patternId } })
  if (patternData == null) {
    return (<div>this mission doesn't exist</div>)
  }

  // import the mission from the data

  return (
    <CloudEditorProvider cloudPattern={patternData}>
      <PatternEditor />
    </CloudEditorProvider>
  )
}
