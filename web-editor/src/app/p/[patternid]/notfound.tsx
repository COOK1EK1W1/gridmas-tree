"use client"

import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"

export default function NotFound() {

  const router = useRouter()
  return (
    <div className="w-full h-full flex items-center justify-center flex-col">
      <p>This mission doesn&apos;t exist</p>
      <div className="">
        <Button onClick={() => router.refresh()}>Retry</Button>
        <Button onClick={() => router.back()}>Go Back</Button>
      </div>
    </div>
  )
}
