import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

function scoreTone(score: number) {
  if (score >= 0.8) return "text-emerald-300 border-emerald-500/40 bg-emerald-500/10"
  if (score >= 0.6) return "text-cyan-300 border-cyan-500/40 bg-cyan-500/10"
  if (score >= 0.4) return "text-amber-300 border-amber-500/40 bg-amber-500/10"
  return "text-rose-300 border-rose-500/40 bg-rose-500/10"
}

export function ScoreBadge({
  score,
  label = "score",
}: {
  score: number | null | undefined
  label?: string
}) {
  if (score == null) {
    return <Badge variant="outline">{label}: n/a</Badge>
  }
  return (
    <Badge variant="outline" className={cn("tabular-nums", scoreTone(score))}>
      {label}: {(score * 100).toFixed(0)}%
    </Badge>
  )
}
