"use client"

import { AlertTriangle, ImageIcon, RefreshCw } from "lucide-react"

import { PageHeader } from "@/components/layout/page-header"
import { StatusPill } from "@/components/workflow/status-pill"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  useAutomationEvents,
  useAutomationOverview,
  useAutomationSessions,
} from "@/hooks/use-console-queries"
import { formatDateTime } from "@/utils/format"

export function AutomationMonitorPage() {
  const limit = 80
  const overview = useAutomationOverview()
  const sessions = useAutomationSessions(limit)
  const events = useAutomationEvents({ limit: 200 })

  return (
    <div className="space-y-4">
      <PageHeader
        title="Automation Monitor"
        description="Live visibility into browser automation sessions, retries, failures, and screenshots."
        right={
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              overview.refetch()
              sessions.refetch()
              events.refetch()
            }}
          >
            <RefreshCw className="mr-2 size-4" />
            Refresh
          </Button>
        }
      />

      <section className="data-grid">
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Active Sessions
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {overview.data?.active_sessions ?? "—"}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Pending Review
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {overview.data?.pending_review ?? "—"}
          </CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Events (fetched)
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">{events.data?.length ?? 0}</CardContent>
        </Card>
        <Card className="panel">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs uppercase tracking-wide text-muted-foreground">
              Screenshot Artifacts
            </CardTitle>
          </CardHeader>
          <CardContent className="text-3xl font-semibold">
            {overview.data?.recent_screenshots.length ?? 0}
          </CardContent>
        </Card>
      </section>

      <Tabs defaultValue="sessions" className="panel p-3">
        <TabsList>
          <TabsTrigger value="sessions">Sessions</TabsTrigger>
          <TabsTrigger value="events">Execution Events</TabsTrigger>
          <TabsTrigger value="screenshots">Screenshots</TabsTrigger>
        </TabsList>

        <TabsContent value="sessions" className="mt-3">
          <ScrollArea className="h-[58vh]">
            <div className="space-y-2 pr-2">
              {sessions.data?.map((session) => (
                <div key={session.application_id} className="rounded-xl border border-border/70 p-3">
                  <div className="flex items-center justify-between">
                    <p className="truncate text-sm font-medium">
                      {session.job_title ?? `Job #${session.job_id}`}
                    </p>
                    <StatusPill status={session.status} />
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">
                    application #{session.application_id} · mode {session.mode}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    updated {formatDateTime(session.updated_at)}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    latest event: {session.latest_event ?? "n/a"}
                  </p>
                </div>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="events" className="mt-3">
          <ScrollArea className="h-[58vh]">
            <div className="space-y-2 pr-2">
              {events.data?.map((event) => (
                <div key={event.id} className="rounded-xl border border-border/70 p-3">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-medium">{event.event_type}</p>
                    <p className="text-xs text-muted-foreground">{formatDateTime(event.created_at)}</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    app #{event.application_id} · job {event.job_title ?? event.job_id ?? "n/a"}
                  </p>
                  {event.payload ? (
                    <pre className="mt-2 overflow-auto rounded-lg bg-muted/40 p-2 text-[11px]">
                      {JSON.stringify(event.payload, null, 2)}
                    </pre>
                  ) : null}
                </div>
              ))}
            </div>
          </ScrollArea>
        </TabsContent>

        <TabsContent value="screenshots" className="mt-3">
          <ScrollArea className="h-[58vh]">
            <div className="space-y-2 pr-2">
              {overview.data?.recent_screenshots.map((screenshot) => (
                <div
                  key={screenshot.path}
                  className="flex items-center justify-between rounded-xl border border-border/70 p-3"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">
                      <ImageIcon className="mr-1 inline size-4" />
                      {screenshot.name}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">{screenshot.path}</p>
                  </div>
                  <div className="text-right text-xs text-muted-foreground">
                    <p>{formatDateTime(screenshot.modified_at)}</p>
                    <p>{(screenshot.size_bytes / 1024).toFixed(1)} KB</p>
                  </div>
                </div>
              ))}
              {!overview.data?.recent_screenshots.length ? (
                <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
                  <AlertTriangle className="mr-2 inline size-4" />
                  No screenshots yet.
                </div>
              ) : null}
            </div>
          </ScrollArea>
        </TabsContent>
      </Tabs>
    </div>
  )
}
