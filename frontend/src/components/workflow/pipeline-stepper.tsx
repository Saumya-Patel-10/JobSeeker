import { Check, ChevronRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const pipeline = [
  "Jobs",
  "Analysis",
  "Resume",
  "Dry Run",
  "Review",
  "Apply",
  "Track",
]

export function PipelineStepper({
  current = 0,
  compact = false,
}: {
  current?: number
  compact?: boolean
}) {
  return (
    <div className={cn("flex flex-wrap items-center gap-2", compact && "gap-1")}>
      {pipeline.map((step, index) => {
        const done = index < current
        const active = index === current
        return (
          <div key={step} className="flex items-center gap-2">
            <Badge
              variant={active ? "default" : "outline"}
              className={cn(
                "rounded-lg px-2.5 py-1 text-[11px]",
                done && "border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
              )}
            >
              {done ? <Check className="mr-1 size-3" /> : null}
              {step}
            </Badge>
            {index < pipeline.length - 1 ? (
              <ChevronRight className="size-3 text-muted-foreground" />
            ) : null}
          </div>
        )
      })}
    </div>
  )
}
