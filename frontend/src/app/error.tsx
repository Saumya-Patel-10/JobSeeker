"use client"

import Link from "next/link"
import { useEffect } from "react"

import { Button, buttonVariants } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  useEffect(() => {
    console.error(error)
  }, [error])

  return (
    <div className="mx-auto flex min-h-[60vh] max-w-md flex-col items-center justify-center gap-4 px-5 text-center">
      <h2 className="text-xl font-semibold tracking-tight">Something went wrong</h2>
      <p className="text-sm text-muted-foreground">
        {error.message || "An unexpected error occurred while rendering this page."}
      </p>
      <div className="flex gap-2">
        <Button onClick={() => reset()}>Try again</Button>
        <Link href="/dashboard" className={cn(buttonVariants({ variant: "outline" }))}>
          Go to dashboard
        </Link>
      </div>
    </div>
  )
}
