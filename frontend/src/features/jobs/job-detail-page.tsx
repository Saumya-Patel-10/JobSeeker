"use client"

import Link from "next/link"
import { Bot, FileText, PlayCircle, Rocket, Workflow } from "lucide-react"
import { Group, Panel, Separator } from "react-resizable-panels"

import { PageHeader } from "@/components/layout/page-header"
import { ScoreBadge } from "@/components/workflow/score-badge"
import { StatusPill } from "@/components/workflow/status-pill"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  useAutomationEvents,
  useAutomationOverview,
  useJobWorkspace,
} from "@/hooks/use-console-queries"
import { formatDateTime } from "@/utils/format"

export function JobDetailPage({ jobId }: { jobId: number }) {
  const workspace = useJobWorkspace(jobId)
  const automationEvents = useAutomationEvents({ limit: 300 })
  const automationOverview = useAutomationOverview()

  if (workspace.isLoading) {
    return <div className="text-sm text-muted-foreground">Loading job workspace...</div>
  }
  if (!workspace.data) {
    return <div className="text-sm text-muted-foreground">Job workspace unavailable.</div>
  }

  const data = workspace.data
  const appIds = new Set(data.applications.map((application) => application.id))
  const relatedEvents = (automationEvents.data ?? []).filter((event) =>
    appIds.has(event.application_id)
  )

  return (
    <div className="space-y-4">
      <PageHeader
        title={data.job.title}
        description={`${data.job.company} · ${data.job.location ?? "Location n/a"} · ${
          data.job.ats_source
        }`}
        right={
          <div className="flex items-center gap-2">
            <StatusPill status={data.job.status} />
            <ScoreBadge score={data.latest_score?.composite} label="composite" />
          </div>
        }
      />

      <Group orientation="horizontal" className="min-h-[58vh] gap-2">
        <Panel defaultSize={33} minSize={20}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm">Job Description + Metadata</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                <div className="rounded-lg border border-border/70 p-2">source: {data.job.ats_source}</div>
                <div className="rounded-lg border border-border/70 p-2">status: {data.job.status}</div>
              </div>
              <div>
                <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Extracted Keywords
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {data.extracted_keywords.slice(0, 30).map((keyword) => (
                    <Badge key={keyword} variant="outline" className="text-[11px]">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
              <ScrollArea className="h-[34vh] rounded-lg border border-border/70 p-2">
                <p className="whitespace-pre-wrap text-sm leading-6 text-muted-foreground">
                  {data.job.description_text}
                </p>
              </ScrollArea>
            </CardContent>
          </Card>
        </Panel>

        <Separator className="w-2 rounded-full bg-border/50 hover:bg-primary/50" />

        <Panel defaultSize={37} minSize={24}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm">AI Fit Analysis</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {data.latest_score ? (
                <>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <ScoreBadge score={data.latest_score.fit_score} label="fit" />
                    <ScoreBadge score={data.latest_score.skill_overlap} label="skills" />
                    <ScoreBadge score={data.latest_score.salary_fit} label="salary" />
                    <ScoreBadge score={data.latest_score.location_compatibility} label="location" />
                    <ScoreBadge
                      score={data.latest_score.seniority_alignment}
                      label="seniority"
                    />
                    <ScoreBadge score={data.latest_score.confidence} label="confidence" />
                  </div>
                  <Card className="border-border/70 bg-muted/20">
                    <CardContent className="p-3">
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                        Reasoning Summary
                      </p>
                      <p className="text-sm text-muted-foreground">{data.latest_score.rationale}</p>
                    </CardContent>
                  </Card>
                  <div className="grid gap-2 sm:grid-cols-2">
                    <Card className="border-border/70 bg-muted/20">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs">Matching Skills</CardTitle>
                      </CardHeader>
                      <CardContent className="flex flex-wrap gap-1.5">
                        {data.latest_score.matched_skills.map((skill) => (
                          <Badge key={skill} variant="secondary" className="text-[11px]">
                            {skill}
                          </Badge>
                        ))}
                      </CardContent>
                    </Card>
                    <Card className="border-border/70 bg-muted/20">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-xs">Missing Skills</CardTitle>
                      </CardHeader>
                      <CardContent className="flex flex-wrap gap-1.5">
                        {data.latest_score.missing_skills.map((skill) => (
                          <Badge key={skill} variant="outline" className="text-[11px]">
                            {skill}
                          </Badge>
                        ))}
                      </CardContent>
                    </Card>
                  </div>
                </>
              ) : (
                <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                  No score yet. Run analyze pipeline from CLI/API to populate this panel.
                </p>
              )}
            </CardContent>
          </Card>
        </Panel>

        <Separator className="w-2 rounded-full bg-border/50 hover:bg-primary/50" />

        <Panel defaultSize={30} minSize={20}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm">Workflow Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <Link href="/resume-studio">
                <Button className="w-full justify-start">
                  <FileText className="mr-2 size-4" />
                  Generate/Review Resume
                </Button>
              </Link>
              <Link href="/automation">
                <Button variant="outline" className="w-full justify-start">
                  <PlayCircle className="mr-2 size-4" />
                  Dry Run + Automation Monitor
                </Button>
              </Link>
              <Link href="/review-queue">
                <Button variant="outline" className="w-full justify-start">
                  <Workflow className="mr-2 size-4" />
                  Open Review Queue
                </Button>
              </Link>
              <Link href={data.job.source_url} target="_blank">
                <Button variant="ghost" className="w-full justify-start">
                  <Rocket className="mr-2 size-4" />
                  Open Job Source
                </Button>
              </Link>
              <Card className="mt-4 border-border/70 bg-muted/20">
                <CardHeader className="pb-2">
                  <CardTitle className="text-xs">Generated Assets</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-xs text-muted-foreground">
                  <p>resume versions: {data.resume_versions.length}</p>
                  <p>applications: {data.applications.length}</p>
                  <p>events: {relatedEvents.length}</p>
                </CardContent>
              </Card>
            </CardContent>
          </Card>
        </Panel>
      </Group>

      <Tabs defaultValue="logs" className="panel p-3">
        <TabsList>
          <TabsTrigger value="logs">Logs</TabsTrigger>
          <TabsTrigger value="reasoning">AI Reasoning</TabsTrigger>
          <TabsTrigger value="screenshots">Screenshots</TabsTrigger>
          <TabsTrigger value="events">Automation Events</TabsTrigger>
          <TabsTrigger value="documents">Generated Documents</TabsTrigger>
        </TabsList>

        <TabsContent value="logs" className="mt-3 space-y-2">
          {relatedEvents.slice(0, 15).map((event) => (
            <div key={event.id} className="rounded-lg border border-border/70 p-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="font-medium">{event.event_type}</span>
                <span className="text-xs text-muted-foreground">{formatDateTime(event.created_at)}</span>
              </div>
              {event.payload ? (
                <pre className="mt-1 overflow-auto rounded bg-muted/40 p-2 text-[11px]">
                  {JSON.stringify(event.payload, null, 2)}
                </pre>
              ) : null}
            </div>
          ))}
        </TabsContent>

        <TabsContent value="reasoning" className="mt-3 space-y-3">
          <Card className="border-border/70 bg-muted/20">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs">
                <Bot className="mr-1 inline size-3.5" />
                Score rationale
              </CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              {data.latest_score?.rationale ?? "No rationale available."}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="screenshots" className="mt-3 space-y-2">
          {automationOverview.data?.recent_screenshots.slice(0, 12).map((screenshot) => (
            <div
              key={screenshot.path}
              className="flex items-center justify-between rounded-lg border border-border/70 p-2"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{screenshot.name}</p>
                <p className="truncate text-xs text-muted-foreground">{screenshot.path}</p>
              </div>
              <span className="text-xs text-muted-foreground">
                {formatDateTime(screenshot.modified_at)}
              </span>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="events" className="mt-3 space-y-2">
          {relatedEvents.map((event) => (
            <div key={event.id} className="rounded-lg border border-border/70 p-2">
              <p className="text-sm font-medium">{event.event_type}</p>
              <p className="text-xs text-muted-foreground">
                application #{event.application_id} · {formatDateTime(event.created_at)}
              </p>
            </div>
          ))}
        </TabsContent>

        <TabsContent value="documents" className="mt-3 space-y-2">
          {data.resume_versions.map((resume) => (
            <div key={resume.id} className="rounded-lg border border-border/70 p-2">
              <p className="text-sm font-medium">
                Resume #{resume.id} · {resume.template}
              </p>
              <p className="text-xs text-muted-foreground">kind: {resume.kind}</p>
              <p className="text-xs text-muted-foreground">
                generated: {formatDateTime(resume.created_at)}
              </p>
              <p className="text-xs text-muted-foreground">pdf: {resume.pdf_path ?? "n/a"}</p>
            </div>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
