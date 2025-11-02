"use client"

import { useEffect, useState } from "react";
import { Dialog, DialogContent, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const displayName = "gridmasPopup"

export default function StartModal() {
  const [displayPopUp, setDisplayPopUp] = useState(false);

  function handleClose() {
    localStorage.setItem(displayName, "true");
    setDisplayPopUp(false)
  }

  useEffect(() => {
    if (localStorage.getItem(displayName) !== "true") {
      setDisplayPopUp(true)
    }
  }, [])
  console.log(displayPopUp)


  return (
    <Dialog open={displayPopUp}>
      <DialogContent>

        <DialogTitle>GRIDmas Tree</DialogTitle>
        <div>
          <p className="py-2">Welcome to GRIDmas Tree, an online viewer and editor for 3D animations for christmas trees</p>
          {//<p className="py-2">Please read over the help page for tips<button className="mx-2 px-2 bg-card rounded-lg" onMouseDown={()=>router.push("/help")}><FaArrowRightLong/></button></p>

          }
          <p className="py-2 text-sm text-gray-600">
            {`By clicking "Get Started", you agree to our `}
            <Link href="/terms" className="text-blue-600 hover:underline">Terms of Service</Link>
            {" "}and{" "}
            <Link href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</Link>.
          </p>
        </div>
        <DialogFooter>
          <Button variant="green" className="w-36" onClick={handleClose}>Get Started<ArrowRight className="ml-1 w-5 h-5" /></Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

