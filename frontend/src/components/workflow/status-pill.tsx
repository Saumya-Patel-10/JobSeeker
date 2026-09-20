import type * as React from "react"

import { Badge } from "@/components/ui/badge"

const variantByStatus: Record<
  string,
  React.ComponentProps<typeof Badge>["variant"]
> = {
  open: "secondary",
  draft: "outline",
  awaiting_review: "secondary",
  submitted: "default",
  interviewing: "default",
  offer: "default",
  accepted: "default",
  rejected: "destructive",
  withdrawn: "ghost",
  closed: "ghost",
  idle: "outline",
  running: "default",
  paused: "secondary",
  stopped: "ghost",
  error: "destructive",
}

export function StatusPill({ status }: { status: string | null | undefined }) {
  const normalized = (status ?? "unknown").toLowerCase()
  const variant = variantByStatus[normalized] ?? "outline"
  return (
    <Badge variant={variant} className="capitalize">
      {normalized.replaceAll("_", " ")}
    </Badge>
  )
}
