import { cn } from "@/lib/utils"

function scoreTone(score: number) {
  if (score >= 0.8) {
    return "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 dark:bg-emerald-500/15"
  }
  if (score >= 0.6) {
    return "border-indigo-500/25 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 dark:bg-indigo-500/15"
  }
  if (score >= 0.4) {
    return "border-amber-500/25 bg-amber-500/10 text-amber-600 dark:text-amber-400 dark:bg-amber-500/15"
  }
  return "border-rose-500/25 bg-rose-500/10 text-rose-600 dark:text-rose-400 dark:bg-rose-500/15"
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
        "inline-flex h-5 items-center rounded-full border px-2.5 text-[11px] font-semibold tabular-nums shadow-2xs",
        scoreTone(score),
        className
      )}
    >
      <span className="opacity-75 mr-1 font-normal">{label}</span>
      {(score * 100).toFixed(0)}%
    </span>
  )
}
