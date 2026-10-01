import { cn } from "@/lib/utils"

type Tone = "success" | "info" | "warning" | "danger" | "neutral"

const toneClass: Record<Tone, string> = {
  success: "border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 dark:bg-emerald-500/15",
  info: "border-indigo-500/20 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 dark:bg-indigo-500/15",
  warning: "border-amber-500/20 bg-amber-500/10 text-amber-600 dark:text-amber-400 dark:bg-amber-500/15",
  danger: "border-rose-500/20 bg-rose-500/10 text-rose-600 dark:text-rose-400 dark:bg-rose-500/15",
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
          tone === "success" && "bg-emerald-500",
          tone === "info" && "bg-indigo-500",
          tone === "warning" && "bg-amber-500",
          tone === "danger" && "bg-rose-500",
          tone === "neutral" && "bg-muted-foreground",
          isLive && "animate-ping"
        )}
      />
      {normalized.replaceAll("_", " ")}
    </span>
  )
}
