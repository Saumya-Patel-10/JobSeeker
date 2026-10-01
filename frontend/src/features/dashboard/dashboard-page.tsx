"use client"

import Link from "next/link"
import { useMemo } from "react"
import {
  ArrowRight,
  BriefcaseBusiness,
  CirclePause,
  CirclePlay,
  ClipboardCheck,
  Inbox,
  Play,
  Send,
  Square,
} from "lucide-react"
import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts"
import { toast } from "sonner"

import { ChartContainer } from "@/components/charts/chart-container"
import { PageHeader } from "@/components/layout/page-header"
import { MetricCard } from "@/components/primitives/metric-card"
import { ScoreBadge } from "@/components/workflow/score-badge"
import { StatusPill } from "@/components/workflow/status-pill"
import { Button, buttonVariants } from "@/components/ui/button"
import {
  useAnalyticsSummary,
  useApplications,
  useApproveCheckpoint,
  useControlCenterActivity,
  useJobHuntStatus,
  usePauseJobHunt,
  usePendingApprovals,
  useResumeJobHunt,
  useSettings,
  useStartJobHunt,
  useStatus,
  useStopJobHunt,
} from "@/hooks/use-console-queries"
import { cn } from "@/lib/utils"
import type { JobHuntMode, PipelineStage, RemotePreference } from "@/types/api"
import { formatRelative } from "@/utils/format"

interface SavedPreferences {
  role_keywords?: string[]
  target_companies?: string[]
  locations?: string[]
  remote_preference?: RemotePreference
  apply?: { daily_limit?: number }
}

const stageLabel: Record<PipelineStage, string> = {
  idle: "Idle",
  discovering: "Discovering jobs",
  ingesting: "Reading postings",
  filtering: "Filtering",
  scoring: "Scoring fit",
  tailoring: "Tailoring resume",
  preparing: "Filling application",
  awaiting_approval: "Waiting for your approval",
  submitting: "Submitting",
  cooldown: "Cooling down",
  sleeping: "Sleeping until next run",
}

const modeLabel: Record<JobHuntMode, string> = {
  manual_review: "Manual review",
  assisted_apply: "Assisted",
  autonomous_apply: "Autonomous",
  linkedin_assist: "LinkedIn assist",
}

function isToday(value: string | null | undefined) {
  if (!value) return false
  const date = new Date(value)
  const now = new Date()
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  )
}

function Section({
  title,
  action,
  children,
  className,
}: {
  title: string
  action?: React.ReactNode
  children: React.ReactNode
  className?: string
}) {
  return (
    <section className={cn("panel", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">{title}</h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </section>
  )
}

function EmptyState({ icon, title, hint }: { icon: React.ReactNode; title: string; hint: string }) {
  return (
    <div className="flex flex-col items-center gap-2 px-4 py-8 text-center">
      <span className="flex size-10 items-center justify-center rounded-full bg-muted text-muted-foreground">
        {icon}
      </span>
      <p className="text-sm font-medium">{title}</p>
      <p className="max-w-xs text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}

function HuntControls() {
  const huntStatus = useJobHuntStatus()
  const settings = useSettings()
  const startHunt = useStartJobHunt()
  const pauseHunt = usePauseJobHunt()
  const resumeHunt = useResumeJobHunt()
  const stopHunt = useStopJobHunt()

  const name = huntStatus.data?.status ?? "idle"
  const isPaused = name === "paused"
  const canStart = name === "idle" || name === "stopped" || name === "error"

  async function handleStart() {
    const prefs = (settings.data?.preferences ?? {}) as SavedPreferences
    try {
      await startHunt.mutateAsync({
        mode: "manual_review",
        run_once: true,
        interval_minutes: null,
        discovery: {
          urls: [],
          keywords: prefs.role_keywords ?? [],
          companies: prefs.target_companies ?? [],
          locations: prefs.locations ?? [],
          remote_preference: prefs.remote_preference ?? "no_preference",
          limit_per_source: 25,
          run_search: true,
        },
      })
      toast.success("Job hunt started")
    } catch {
      toast.error("Could not start the hunt. Is the backend running?")
    }
  }

  async function handlePauseResume() {
    try {
      if (isPaused) {
        await resumeHunt.mutateAsync()
        toast.success("Job hunt resumed")
      } else {
        await pauseHunt.mutateAsync()
        toast.success("Job hunt paused")
      }
    } catch {
      toast.error("Action failed")
    }
  }

  async function handleStop() {
    try {
      await stopHunt.mutateAsync()
      toast.success("Job hunt stopped")
    } catch {
      toast.error("Action failed")
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-2">
      {canStart ? (
        <Button className="h-9 gap-1.5 px-4" onClick={handleStart} disabled={startHunt.isPending}>
          <Play className="size-4" />
          {startHunt.isPending ? "Starting..." : "Start hunt"}
        </Button>
      ) : (
        <>
          <Button variant="outline" className="h-9 gap-1.5 px-3" onClick={handlePauseResume}>
            {isPaused ? <CirclePlay className="size-4" /> : <CirclePause className="size-4" />}
            {isPaused ? "Resume" : "Pause"}
          </Button>
          <Button variant="outline" className="h-9 gap-1.5 px-3" onClick={handleStop}>
            <Square className="size-4" />
            Stop
          </Button>
        </>
      )}
      <Link
        href="/control-center"
        className={cn(buttonVariants({ variant: "ghost" }), "h-9 px-3 text-muted-foreground")}
      >
        Configure
      </Link>
    </div>
  )
}

function HuntStatusCard() {
  const huntStatus = useJobHuntStatus()
  const data = huntStatus.data
  const name = data?.status ?? "idle"
  const active = name === "running" || name === "paused"
  const stage = data?.stage ?? "idle"
  const stats = data?.stats

  const counters = [
    { label: "Seen", value: stats?.jobs_seen ?? 0 },
    { label: "Scored", value: stats?.jobs_analyzed ?? 0 },
    { label: "Tailored", value: stats?.resumes_generated ?? 0 },
    { label: "Prepared", value: stats?.applications_prepared ?? stats?.applications_attempted ?? 0 },
    { label: "Submitted", value: stats?.applications_submitted ?? 0 },
  ]

  return (
    <section className="panel p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0 space-y-1.5">
          <div className="flex items-center gap-2">
            <h2 className="text-sm font-semibold">Job hunt</h2>
            <StatusPill status={name} />
            {data?.mode ? (
              <span className="text-xs text-muted-foreground">{modeLabel[data.mode]}</span>
            ) : null}
          </div>
          <p className="truncate text-sm text-muted-foreground">
            {active
              ? data?.current_job_title
                ? `${stageLabel[stage]}: ${data.current_job_title}${data.current_company ? ` at ${data.current_company}` : ""}`
                : stageLabel[stage]
              : "Nothing running. Start a hunt to discover, score, and prepare applications."}
          </p>
          {data?.last_error ? (
            <p className="text-xs text-destructive">Last error: {data.last_error}</p>
          ) : null}
        </div>
        <HuntControls />
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-lg border border-border bg-border sm:grid-cols-5">
        {counters.map((counter) => (
          <div key={counter.label} className="bg-card px-4 py-3">
            <dt className="text-xs text-muted-foreground">{counter.label}</dt>
            <dd className="mt-0.5 text-lg font-semibold tabular">{counter.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  )
}

export function DashboardPage() {
  const analytics = useAnalyticsSummary()
  const applications = useApplications({ limit: 200 })
  const approvals = usePendingApprovals()
  const activity = useControlCenterActivity(10)
  const status = useStatus()
  const settings = useSettings()
  const approve = useApproveCheckpoint()

  const dailyLimit = ((settings.data?.preferences ?? {}) as SavedPreferences).apply?.daily_limit ?? 20
  const submittedToday = useMemo(
    () => (applications.data ?? []).filter((a) => isToday(a.submitted_at)).length,
    [applications.data]
  )
  const quotaPct = Math.min(100, Math.round((submittedToday / Math.max(1, dailyLimit)) * 100))
  const pending = approvals.data ?? []
  const recent = (applications.data ?? []).slice(0, 7)

  const health = [
    { label: "Backend", ok: Boolean(status.data?.healthy), okText: "Connected", badText: "Offline" },
    {
      label: "Language model",
      ok: Boolean(status.data?.llm_reachable),
      okText: status.data?.llm_provider ?? "Online",
      badText: "Not reachable",
    },
    {
      label: "Browser session",
      ok: Boolean(status.data?.browser_profile_has_cookies),
      okText: "Logged-in session ready",
      badText: "No saved logins",
    },
    {
      label: "Database",
      ok: Boolean(status.data?.db_exists),
      okText: "Ready",
      badText: "Missing",
    },
  ]

  async function handleApprove(id: number) {
    try {
      await approve.mutateAsync({ id, submit: false })
      toast.success("Approved")
    } catch {
      toast.error("Could not approve this application")
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="What your assistant found, prepared, and sent."
      />

      <HuntStatusCard />

      <section className="data-grid">
        <div className="panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Submitted today</p>
            <Send className="size-4 text-muted-foreground" />
          </div>
          <p className="text-2xl font-semibold tracking-tight tabular">
            {submittedToday}
            <span className="text-base font-normal text-muted-foreground"> / {dailyLimit}</span>
          </p>
          <div
            className="mt-3 h-1.5 overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-label="Daily application limit used"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={quotaPct}
          >
            <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${quotaPct}%` }} />
          </div>
        </div>
        <MetricCard
          label="Needs your review"
          value={pending.length}
          icon={<ClipboardCheck className="size-4" />}
          hint={pending.length ? "Open Applications to approve" : "You are all caught up"}
        />
        <MetricCard
          label="Jobs found today"
          value={analytics.data?.jobs_ingested_today ?? "-"}
          icon={<BriefcaseBusiness className="size-4" />}
          hint={`${analytics.data?.total_jobs ?? 0} jobs in total`}
        />
        <MetricCard
          label="Total applications"
          value={analytics.data?.total_applications ?? "-"}
          icon={<Inbox className="size-4" />}
          hint="All time"
        />
      </section>

      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Section
            title="Needs your review"
            action={
              <Link
                href="/review-queue"
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                Open queue <ArrowRight className="size-3" />
              </Link>
            }
          >
            {pending.length === 0 ? (
              <EmptyState
                icon={<ClipboardCheck className="size-5" />}
                title="Nothing waiting on you"
                hint="Prepared applications stop here so you can check the resume and answers before anything is sent."
              />
            ) : (
              <ul className="-my-2 divide-y divide-border">
                {pending.slice(0, 5).map((item) => (
                  <li key={item.id} className="flex items-center gap-3 py-3">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{item.role}</p>
                      <p className="truncate text-xs text-muted-foreground">{item.company}</p>
                    </div>
                    {item.confidence != null ? (
                      <ScoreBadge score={item.confidence} label="confidence" className="hidden sm:inline-flex" />
                    ) : null}
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleApprove(item.id)}
                      disabled={approve.isPending}
                    >
                      Approve
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section
            title="Recent applications"
            action={
              <Link
                href="/jobs"
                className="inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline"
              >
                All jobs <ArrowRight className="size-3" />
              </Link>
            }
          >
            {recent.length === 0 ? (
              <EmptyState
                icon={<Send className="size-5" />}
                title="No applications yet"
                hint="Start a hunt and prepared applications will show up here."
              />
            ) : (
              <div className="-mx-4 -my-4 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs text-muted-foreground">
                      <th className="px-4 py-2.5 font-medium">Role</th>
                      <th className="px-4 py-2.5 font-medium">Status</th>
                      <th className="hidden px-4 py-2.5 font-medium sm:table-cell">Mode</th>
                      <th className="px-4 py-2.5 text-right font-medium">Created</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {recent.map((application) => (
                      <tr key={application.id} className="transition-colors hover:bg-muted/40">
                        <td className="max-w-[16rem] px-4 py-3">
                          <Link
                            href={`/jobs/${application.job_id}`}
                            className="block truncate font-medium hover:text-primary"
                          >
                            {application.job_title ?? `Job #${application.job_id}`}
                          </Link>
                        </td>
                        <td className="px-4 py-3">
                          <StatusPill status={application.status} />
                        </td>
                        <td className="hidden px-4 py-3 text-muted-foreground capitalize sm:table-cell">
                          {application.mode.replaceAll("_", " ")}
                        </td>
                        <td className="px-4 py-3 text-right text-xs text-muted-foreground whitespace-nowrap">
                          {formatRelative(application.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Section>

          <Section title="Last 14 days">
            <ChartContainer height={220}>
              <BarChart data={analytics.data?.timeline_14d ?? []}>
                <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="var(--color-border)" />
                <XAxis
                  dataKey="day"
                  tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(value: string) => value.slice(5)}
                  label={{ value: "Date", position: "insideBottom", offset: -2, fontSize: 11 }}
                  height={36}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11, fill: "var(--color-muted-foreground)" }}
                  tickLine={false}
                  axisLine={false}
                  width={32}
                />
                <Tooltip
                  cursor={{ fill: "var(--color-muted)" }}
                  contentStyle={{
                    background: "var(--color-popover)",
                    border: "1px solid var(--color-border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="jobs" name="Jobs found" fill="var(--color-chart-2)" radius={[4, 4, 0, 0]} />
                <Bar
                  dataKey="applications"
                  name="Applications"
                  fill="var(--color-chart-1)"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ChartContainer>
          </Section>
        </div>

        <div className="space-y-6">
          <Section title="Activity">
            {(activity.data ?? []).length === 0 ? (
              <EmptyState
                icon={<Inbox className="size-5" />}
                title="No activity yet"
                hint="Discovery, scoring, and application events appear here as they happen."
              />
            ) : (
              <ol className="relative space-y-4 border-l border-border pl-5">
                {(activity.data ?? []).slice(0, 8).map((entry) => (
                  <li key={`${entry.timestamp}-${entry.title}`} className="relative">
                    <span className="absolute -left-[25px] top-1.5 size-2 rounded-full bg-primary" />
                    <p className="text-sm leading-snug">{entry.title}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {formatRelative(entry.timestamp)}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </Section>

          <Section title="System">
            <ul className="space-y-3">
              {health.map((item) => (
                <li key={item.label} className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-muted-foreground">{item.label}</span>
                  <span className="inline-flex items-center gap-2 font-medium">
                    <span
                      className={cn("size-1.5 rounded-full", item.ok ? "bg-success" : "bg-warning")}
                      aria-hidden="true"
                    />
                    {item.ok ? item.okText : item.badText}
                  </span>
                </li>
              ))}
            </ul>
          </Section>
        </div>
      </div>
    </div>
  )
}
