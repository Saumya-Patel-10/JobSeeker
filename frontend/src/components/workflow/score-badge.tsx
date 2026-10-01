import { cn } from "@/lib/utils"

function scoreTone(score: number) {
  if (score >= 0.8) return "border-success/25 bg-success/10 text-success"
  if (score >= 0.6) return "border-info/25 bg-info/10 text-info"
  if (score >= 0.4) return "border-warning/30 bg-warning/15 text-warning"
  return "border-destructive/25 bg-destructive/10 text-destructive"
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
          "inline-flex h-5 items-center rounded-full border border-border/80 bg-muted/60 px-2 text-[11px] font-medium text-muted-foreground",
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
        "inline-flex h-5 items-center rounded-full border px-2.5 text-[11px] font-semibold tabular-nums",
        scoreTone(score),
        className
      )}
    >
      <span className="mr-1 font-normal opacity-75">{label}</span>
      {(score * 100).toFixed(0)}%
    </span>
  )
}
