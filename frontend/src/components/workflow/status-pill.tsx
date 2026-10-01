import { cn } from "@/lib/utils"

type Tone = "success" | "info" | "warning" | "danger" | "neutral"

const toneClass: Record<Tone, string> = {
  success: "border-success/25 bg-success/10 text-success",
  info: "border-info/25 bg-info/10 text-info",
  warning: "border-warning/30 bg-warning/15 text-warning",
  danger: "border-destructive/25 bg-destructive/10 text-destructive",
  neutral: "border-border/80 bg-muted/60 text-muted-foreground",
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
  const isLive = normalized === "running"

  return (
    <span
      className={cn(
        "inline-flex h-5 items-center gap-1.5 rounded-full border px-2.5 text-[11px] font-semibold whitespace-nowrap capitalize shadow-2xs",
        toneClass[tone],
        className
      )}
    >
      <span
        className={cn(
          "size-1.5 rounded-full",
          tone === "success" && "bg-success",
          tone === "info" && "bg-info",
          tone === "warning" && "bg-warning",
          tone === "danger" && "bg-destructive",
          tone === "neutral" && "bg-muted-foreground",
          isLive && "animate-ping"
        )}
      />
      {normalized.replaceAll("_", " ")}
    </span>
  )
}
