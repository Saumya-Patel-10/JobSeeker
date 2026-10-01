import type * as React from "react"

import { cn } from "@/lib/utils"

interface MetricCardProps {
  label: string
  value: React.ReactNode
  hint?: React.ReactNode
  icon?: React.ReactNode
  className?: string
}

export function MetricCard({ label, value, hint, icon, className }: MetricCardProps) {
  return (
    <section className={cn("panel p-4", className)}>
      <div className="mb-3 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{label}</p>
        {icon ? <div className="text-muted-foreground">{icon}</div> : null}
      </div>
      <p className="text-2xl font-semibold tracking-tight tabular">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </section>
  )
}
