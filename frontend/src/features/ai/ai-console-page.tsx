"use client"

import { useMemo, useState } from "react"
import { BrainCircuit, ShieldAlert, Timer } from "lucide-react"

import { PageHeader } from "@/components/layout/page-header"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { useAIActivity, useAISummary } from "@/hooks/use-console-queries"
import { formatDateTime } from "@/utils/format"

export function AIConsolePage() {
  const [search, setSearch] = useState("")
  const activity = useAIActivity(350)
  const summary = useAISummary(350)

  const filtered = useMemo(() => {
    const rows = activity.data ?? []
    if (!search) return rows
    const query = search.toLowerCase()
    return rows.filter((row) =>
      `${row.event} ${row.logger} ${JSON.stringify(row.payload)}`.toLowerCase().includes(query)
    )
  }, [activity.data, search])

  return (
    <div className="space-y-4">
      <PageHeader
        title="AI Activity Console"
        description="Trace LLM requests, structured outputs, validation outcomes, and latency signals."
      />

      <section className="data-grid">
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Logged AI Entries
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            <BrainCircuit className="mr-2 inline size-5 text-primary" />
            {summary.data?.total_entries ?? "—"}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Validation Flags
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            <ShieldAlert className="mr-2 inline size-5 text-amber-400" />
            {summary.data?.validation_failures ?? "—"}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Average Latency
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            <Timer className="mr-2 inline size-5 text-cyan-400" />
            {summary.data?.avg_latency_ms != null ? `${summary.data.avg_latency_ms} ms` : "n/a"}
          </CardContent>
        </Card>
      </section>

      <Card className="panel">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">LLM Trace Stream</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder="Filter events, loggers, payload..."
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <ScrollArea className="h-[60vh]">
            <div className="space-y-2 pr-2">
              {filtered.map((entry) => (
                <div key={`${entry.timestamp}-${entry.event}`} className="rounded-xl border border-border/70 p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{entry.event}</p>
                    <p className="text-xs text-muted-foreground">{formatDateTime(entry.timestamp)}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    logger: {entry.logger} · level: {entry.level}
                  </p>
                  {Object.keys(entry.payload).length ? (
                    <pre className="mt-2 overflow-auto rounded-lg bg-muted/40 p-2 text-[11px]">
                      {JSON.stringify(entry.payload, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ))}
              {!filtered.length ? (
                <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
                  No AI traces found for this filter.
                </div>
              ) : null}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}
