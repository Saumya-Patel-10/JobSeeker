import { cn } from "@/lib/utils"

type Tone = "success" | "info" | "warning" | "danger" | "neutral"

const toneClass: Record<Tone, string> = {
  success: "bg-success/10 text-success",
  info: "bg-info/10 text-info",
  warning: "bg-warning/15 text-warning",
  danger: "bg-destructive/10 text-destructive",
  neutral: "bg-muted text-muted-foreground",
}

const toneByStatus: Record<string, Tone> = {
  submitted: "success",
  interviewing: "success",
  offer: "success",
  accepted: "success",
  approved: "success",
  running: "success",
  open: "info",
  tailoring: "info",
  preparing: "info",
  scoring: "info",
  applying: "info",
  awaiting_review: "warning",
  awaiting_approval: "warning",
  pending: "warning",
  paused: "warning",
  rejected: "danger",
  failed: "danger",
  error: "danger",
  draft: "neutral",
  idle: "neutral",
  stopped: "neutral",
  closed: "neutral",
  withdrawn: "neutral",
  skipped: "neutral",
}

export function StatusPill({
  status,
  className,
}: {
  status: string | null | undefined
  className?: string
}) {
  const normalized = (status ?? "unknown").toLowerCase()
  const tone = toneByStatus[normalized] ?? "neutral"
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded-full px-2 text-xs font-medium whitespace-nowrap capitalize",
        toneClass[tone],
        className
      )}
    >
      {normalized.replaceAll("_", " ")}
    </span>
  )
}
