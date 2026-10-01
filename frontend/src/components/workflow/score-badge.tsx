import { cn } from "@/lib/utils"

function scoreTone(score: number) {
  if (score >= 0.8) return "bg-success/10 text-success"
  if (score >= 0.6) return "bg-info/10 text-info"
  if (score >= 0.4) return "bg-warning/15 text-warning"
  return "bg-destructive/10 text-destructive"
}

export function ScoreBadge({
  score,
  label = "score",
  className,
}: {
  score: number | null | undefined
  label?: string
  className?: string
}) {
  if (score == null) {
    return (
      <span
        className={cn(
          "inline-flex h-5 items-center rounded-full bg-muted px-2 text-xs font-medium text-muted-foreground",
          className
        )}
      >
        {label}: n/a
      </span>
    )
  }
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center rounded-full px-2 text-xs font-medium tabular-nums",
        scoreTone(score),
        className
      )}
    >
      {label}: {(score * 100).toFixed(0)}%
    </span>
  )
}
