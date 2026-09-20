"use client"

import Link from "next/link"
import { Activity, BriefcaseBusiness, Clock3, FileText, Inbox } from "lucide-react"
import { motion } from "framer-motion"
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { ChartContainer } from "@/components/charts/chart-container"
import { PageHeader } from "@/components/layout/page-header"
import { MetricCard } from "@/components/primitives/metric-card"
import { PipelineStepper } from "@/components/workflow/pipeline-stepper"
import { ScoreBadge } from "@/components/workflow/score-badge"
import { StatusPill } from "@/components/workflow/status-pill"
import { Button } from "@/components/ui/button"
import {
  useAIActivity,
  useAISummary,
  useAnalyticsSummary,
  useApplications,
  useAutomationOverview,
  useJobs,
  useStatus,
} from "@/hooks/use-console-queries"
import { formatRelative } from "@/utils/format"

export function DashboardPage() {
  const analytics = useAnalyticsSummary()
  const applications = useApplications({ limit: 20 })
  const jobs = useJobs({ limit: 12 })
  const automation = useAutomationOverview()
  const aiSummary = useAISummary(250)
  const aiActivity = useAIActivity(30)
  const status = useStatus()

  return (
    <div className="space-y-4">
      <PageHeader
        title="Operations Dashboard"
        description="Centralized view of ingestion, AI analysis, resume generation, and approval queues."
        right={<PipelineStepper current={1} compact />}
      />

      <section className="data-grid">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}>
          <MetricCard
            label="Jobs Ingested Today"
            value={analytics.data?.jobs_ingested_today ?? "—"}
            icon={<BriefcaseBusiness className="size-4" />}
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
        >
          <MetricCard
            label="Pending Review"
            value={analytics.data?.applications_pending_review ?? "—"}
            icon={<Inbox className="size-4" />}
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <MetricCard
            label="Active Automation Sessions"
            value={automation.data?.active_sessions ?? "—"}
            icon={<Activity className="size-4" />}
            hint={`Recent screenshots: ${automation.data?.recent_screenshots.length ?? 0}`}
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
        >
          <MetricCard
            label="AI Activity (24h window)"
            value={aiSummary.data?.total_entries ?? "—"}
            icon={<Clock3 className="size-4" />}
            hint={
              aiSummary.data?.avg_latency_ms != null
                ? `Avg latency ${aiSummary.data.avg_latency_ms} ms`
                : "No latency samples yet"
            }
          />
        </motion.div>
      </section>

      <section className="panel p-4">
        <h3 className="mb-3 text-sm font-semibold">Runtime Health</h3>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-lg border border-border/70 p-3">
            <p className="text-xs text-muted-foreground">Backend</p>
            <p className="text-sm font-medium">{status.data?.healthy ? "reachable" : "offline"}</p>
          </div>
          <div className="rounded-lg border border-border/70 p-3">
            <p className="text-xs text-muted-foreground">LLM</p>
            <p className="text-sm font-medium">
              {status.data?.llm_reachable ? "reachable" : "not reachable"}
            </p>
          </div>
          <div className="rounded-lg border border-border/70 p-3">
            <p className="text-xs text-muted-foreground">Browser Session</p>
            <p className="text-sm font-medium">
              {status.data?.browser_profile_has_cookies ? "cookie session ready" : "needs login"}
            </p>
          </div>
          <div className="rounded-lg border border-border/70 p-3">
            <p className="text-xs text-muted-foreground">Database</p>
            <p className="text-sm font-medium">{status.data?.db_exists ? "ready" : "missing"}</p>
          </div>
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <article className="panel p-4 xl:col-span-2">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Application Funnel</h3>
            <span className="text-xs text-muted-foreground">
              Total {analytics.data?.total_applications ?? 0}
            </span>
          </div>
          <ChartContainer>
            <BarChart data={analytics.data?.funnel ?? []}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.15} />
              <XAxis dataKey="stage" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="count" radius={[6, 6, 0, 0]} fill="var(--color-chart-1)" />
            </BarChart>
          </ChartContainer>
        </article>

        <article className="panel p-4">
          <h3 className="mb-3 text-sm font-semibold">Score Distribution</h3>
          <div className="space-y-2">
            {analytics.data?.score_distribution.map((bucket) => (
              <div key={bucket.label} className="flex items-center justify-between rounded-lg bg-muted/30 p-2">
                <span className="text-xs text-muted-foreground">{bucket.label}</span>
                <span className="text-sm font-medium">{bucket.count}</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <article className="panel p-4">
          <h3 className="mb-3 text-sm font-semibold">Ingestion and Submission Timeline</h3>
          <ChartContainer>
            <AreaChart data={analytics.data?.timeline_14d ?? []}>
              <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.12} />
              <XAxis dataKey="day" tick={{ fontSize: 11 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Area
                type="monotone"
                dataKey="jobs"
                stackId="a"
                stroke="var(--color-chart-2)"
                fill="var(--color-chart-2)"
                fillOpacity={0.35}
              />
              <Area
                  type="monotone"
                  dataKey="applications"
                  stackId="a"
                  stroke="var(--color-chart-3)"
                  fill="var(--color-chart-3)"
                  fillOpacity={0.35}
                />
            </AreaChart>
          </ChartContainer>
        </article>

        <article className="panel p-4">
          <h3 className="mb-3 text-sm font-semibold">Recent AI Activity</h3>
          <div className="space-y-2">
            {aiActivity.data?.slice(0, 8).map((entry) => (
              <div key={`${entry.timestamp}-${entry.event}`} className="rounded-lg border border-border/70 p-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">{entry.event}</span>
                  <span className="text-[11px] text-muted-foreground">{formatRelative(entry.timestamp)}</span>
                </div>
                <p className="text-xs text-muted-foreground">{entry.logger}</p>
              </div>
            ))}
            {!aiActivity.data?.length ? (
              <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                No AI activity yet. Run ingestion/analyze/tailor to start traces.
              </p>
            ) : null}
          </div>
        </article>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <article className="panel p-4">
          <h3 className="mb-3 text-sm font-semibold">Recent Jobs</h3>
          <div className="space-y-2">
            {jobs.data?.slice(0, 8).map((job) => (
              <div key={job.id} className="flex items-center justify-between rounded-lg border border-border/70 p-2">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{job.title}</p>
                  <p className="truncate text-xs text-muted-foreground">
                    {job.company} · {job.location ?? "Location n/a"}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusPill status={job.status} />
                  <span className="text-[11px] text-muted-foreground">{job.ats_source}</span>
                </div>
              </div>
            ))}
          </div>
        </article>

        <article className="panel p-4">
          <h3 className="mb-3 text-sm font-semibold">Pending Review Queue</h3>
          <div className="space-y-2">
            {applications.data?.map((application) => (
              <div
                key={application.id}
                className="flex items-center justify-between rounded-lg border border-border/70 p-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium">{application.job_title ?? `Job #${application.job_id}`}</p>
                  <p className="text-xs text-muted-foreground">Application #{application.id}</p>
                </div>
                <div className="flex items-center gap-2">
                  <StatusPill status={application.status} />
                  <ScoreBadge score={application.status === "submitted" ? 1 : 0.6} label={application.mode} />
                </div>
              </div>
            ))}
            {!applications.data?.length ? (
              <div className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
                No applications found yet.
              </div>
            ) : null}
          </div>
        </article>
      </section>
      <section className="panel p-4">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold">Recent Generated Resumes</h3>
          <div className="flex items-center gap-2">
            <Link href="/jobs">
              <Button variant="outline" size="sm">
                Open Jobs Explorer
              </Button>
            </Link>
            <Link href="/review-queue">
              <Button variant="outline" size="sm">
                Open Review Queue
              </Button>
            </Link>
          </div>
        </div>
        <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
          {(jobs.data ?? [])
            .filter((job) => job.resume_versions > 0)
            .slice(0, 9)
            .map((job) => (
              <div key={job.id} className="rounded-xl border border-border/70 p-3">
              <div className="mb-1 flex items-center justify-between text-sm font-medium">
                  <span className="truncate">{job.title}</span>
                  <FileText className="size-4 text-muted-foreground" />
              </div>
                <p className="text-xs text-muted-foreground">
                  {job.company} · versions: {job.resume_versions}
                </p>
                <p className="mt-1 text-xs text-muted-foreground">
                  applications: {job.applications_count}
                </p>
              </div>
            ))}
          {(jobs.data ?? []).every((job) => job.resume_versions === 0) ? (
            <p className="rounded-lg border border-dashed border-border p-4 text-sm text-muted-foreground">
              No generated resumes yet. Run `generate-resume` from CLI or API pipeline.
            </p>
          ) : null}
        </div>
      </section>
    </div>
  )
}
