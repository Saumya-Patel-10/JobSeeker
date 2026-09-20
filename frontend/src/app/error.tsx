"use client"

import { useEffect } from "react"

import { Button } from "@/components/ui/button"

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
    <div className="panel flex min-h-64 flex-col items-start justify-center gap-3 p-6">
      <h2 className="text-xl font-semibold">Something went wrong</h2>
      <p className="text-sm text-muted-foreground">
        {error.message || "Unknown frontend error while rendering the operations console."}
      </p>
      <Button onClick={() => reset()}>Retry</Button>
    </div>
  )
}
