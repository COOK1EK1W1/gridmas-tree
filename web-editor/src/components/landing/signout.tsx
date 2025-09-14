"use client"

import { signOut } from "@/util/auth-client"
import { Dot } from "lucide-react"
import { useRouter } from "next/navigation"
import { useTransition } from "react"

export default function SignoutBit({ userData }: { userData: any }) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const handleSignout = () => {
    startTransition(async () => {
      let a = await signOut()
      if (a.data) {
        router.push("")
      }
    })
  }
  if (userData) {
    return (

      <span className="flex font-semibold">
        <span className="hidden lg:inline">{userData.user.email} <Dot className="inline-block" /></span>
        <span onClick={handleSignout}>Sign Out</span>
      </span>
    )
  } else return null

}
