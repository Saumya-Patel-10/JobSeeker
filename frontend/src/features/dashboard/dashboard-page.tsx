"use client"

import Link from "next/link"
import { useMemo, useState } from "react"
import {
  ArrowRight,
  BriefcaseBusiness,
  CirclePause,
  CirclePlay,
  ClipboardCheck,
  Compass,
  Cpu,
  Inbox,
  Layers,
  Play,
  Send,
  Sparkles,
  Square,
} from "lucide-react"
import { Bar, BarChart, CartesianGrid, Legend, Tooltip, XAxis, YAxis } from "recharts"
import { toast } from "sonner"

import { ChartContainer } from "@/components/charts/chart-container"
import { PageHeader } from "@/components/layout/page-header"
import { ScoreBadge } from "@/components/workflow/score-badge"
import { StatusPill } from "@/components/workflow/status-pill"
import { Button, buttonVariants } from "@/components/ui/button"
import {
  ROLE_TRACKS,
  TRACK_LIST,
  RoleTrackId,
  identifyJobTracks,
} from "@/features/jobs/role-tracks"
import {
  useAnalyticsSummary,
  useApplications,
  useApproveCheckpoint,
  useControlCenterActivity,
  useJobHuntStatus,
  useJobs,
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
  filtering: "Filtering qualifications",
  scoring: "Scoring AI fit",
  tailoring: "Tailoring resume",
  preparing: "Filling application form",
  awaiting_approval: "Awaiting your review",
  submitting: "Submitting application",
  cooldown: "Cooling down",
  sleeping: "Scheduled next run",
}

const pipelineSteps: PipelineStage[] = [
  "discovering",
  "ingesting",
  "filtering",
  "scoring",
  "tailoring",
  "preparing",
  "awaiting_approval",
  "submitting",
]

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
    <section className={cn("panel shadow-sm", className)}>
      <div className="flex items-center justify-between gap-3 border-b border-border/80 px-5 py-3.5">
        <h2 className="text-sm font-semibold tracking-tight">{title}</h2>
        {action}
      </div>
      <div className="p-5">{children}</div>
    </section>
  )
}

function EmptyState({ icon, title, hint }: { icon: React.ReactNode; title: string; hint: string }) {
  return (
    <div className="flex flex-col items-center gap-2.5 px-4 py-10 text-center">
      <span className="flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        {icon}
      </span>
      <p className="text-sm font-semibold">{title}</p>
      <p className="max-w-xs text-xs text-muted-foreground">{hint}</p>
    </div>
  )
}

export function DashboardPage() {
  const analytics = useAnalyticsSummary()
  const applications = useApplications({ limit: 200 })
  const approvals = usePendingApprovals()
  const activity = useControlCenterActivity(12)
  const status = useStatus()
  const settings = useSettings()
  const approve = useApproveCheckpoint()
  const allJobs = useJobs({ limit: 300 })

  const huntStatus = useJobHuntStatus()
  const startHunt = useStartJobHunt()
  const pauseHunt = usePauseJobHunt()
  const resumeHunt = useResumeJobHunt()
  const stopHunt = useStopJobHunt()

  const [selectedTrack, setSelectedTrack] = useState<RoleTrackId>("all")

  const huntData = huntStatus.data
  const huntState = huntData?.status ?? "idle"
  const isHuntActive = huntState === "running" || huntState === "paused"
  const isHuntPaused = huntState === "paused"
  const currentStage = huntData?.stage ?? "idle"
  const stats = huntData?.stats

  const dailyLimit = ((settings.data?.preferences ?? {}) as SavedPreferences).apply?.daily_limit ?? 20
  const submittedToday = useMemo(
    () => (applications.data ?? []).filter((a) => isToday(a.submitted_at)).length,
    [applications.data]
  )
  const quotaPct = Math.min(100, Math.round((submittedToday / Math.max(1, dailyLimit)) * 100))
  const pending = approvals.data ?? []
  const recent = (applications.data ?? []).slice(0, 7)

  // Track breakdown of ingested jobs
  const trackCounts = useMemo(() => {
    const counts: Record<RoleTrackId, number> = {
      all: allJobs.data?.length ?? 0,
      frontend: 0,
      backend: 0,
      fullstack: 0,
      ai: 0,
    }
    for (const job of allJobs.data ?? []) {
      const tracks = identifyJobTracks(job)
      for (const t of tracks) {
        counts[t] = (counts[t] || 0) + 1
      }
    }
    return counts
  }, [allJobs.data])

  const counters = [
    { label: "Jobs Discovered", value: stats?.jobs_seen ?? 0, icon: Compass },
    { label: "AI Scored", value: stats?.jobs_analyzed ?? 0, icon: Sparkles },
    { label: "Resumes Tailored", value: stats?.resumes_generated ?? 0, icon: Layers },
    { label: "Applications Prepared", value: stats?.applications_prepared ?? stats?.applications_attempted ?? 0, icon: ClipboardCheck },
    { label: "Submitted", value: stats?.applications_submitted ?? 0, icon: Send },
  ]

  const health = [
    { label: "Backend API", ok: Boolean(status.data?.healthy), okText: "Connected (FastAPI)", badText: "Offline" },
    {
      label: "Language Model",
      ok: Boolean(status.data?.llm_reachable),
      okText: status.data?.llm_provider ? `${status.data.llm_provider} (LM Studio)` : "Online",
      badText: "Not reachable",
    },
    {
      label: "Browser Session",
      ok: Boolean(status.data?.browser_profile_has_cookies),
      okText: "Firefox profile ready",
      badText: "No saved session",
    },
    {
      label: "Database",
      ok: Boolean(status.data?.db_exists),
      okText: "SQLite initialized",
      badText: "Missing",
    },
  ]

  async function handleStartHunt(trackId: RoleTrackId = selectedTrack) {
    const prefs = (settings.data?.preferences ?? {}) as SavedPreferences
    const trackKeywords = ROLE_TRACKS[trackId].keywords

    try {
      await startHunt.mutateAsync({
        mode: "manual_review",
        run_once: true,
        interval_minutes: null,
        discovery: {
          urls: [],
          keywords: trackId === "all" ? (prefs.role_keywords?.length ? prefs.role_keywords : trackKeywords) : trackKeywords,
          companies: prefs.target_companies ?? [],
          locations: prefs.locations ?? [],
          remote_preference: prefs.remote_preference ?? "no_preference",
          limit_per_source: 30,
          run_search: true,
        },
      })
      toast.success(`Job hunt started for ${ROLE_TRACKS[trackId].label}`)
    } catch {
      toast.error("Could not start the hunt. Is the backend running?")
    }
  }

  async function handlePauseResume() {
    try {
      if (isHuntPaused) {
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

  async function handleApprove(id: number) {
    try {
      await approve.mutateAsync({ id, submit: false })
      toast.success("Checkpoint approved")
    } catch {
      toast.error("Could not approve this application")
    }
  }

  return (
    <div className="space-y-6">
      {/* Header with Title and Track Summary */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          title="Command Deck"
          description="Autonomous & supervised job discovery across Frontend, Backend, Full-Stack, and AI Development."
        />
        <div className="flex items-center gap-2">
          <Link
            href="/jobs"
            className={cn(
              buttonVariants({ variant: "outline", size: "sm" }),
              "rounded-xl border-border/80 bg-card/60 shadow-xs hover:border-primary/40"
            )}
          >
            <BriefcaseBusiness className="mr-2 size-3.5 text-primary" />
            Explore All Jobs ({allJobs.data?.length ?? 0})
          </Link>
          <Link
            href="/control-center"
            className={cn(
              buttonVariants({ variant: "outline", size: "sm" }),
              "rounded-xl border-border/80 bg-card/60 shadow-xs hover:border-primary/40"
            )}
          >
            <Layers className="mr-2 size-3.5 text-primary" />
            Hunt Settings
          </Link>
        </div>
      </div>

      {/* Hero Command Deck Card */}
      <div className="relative overflow-hidden rounded-2xl border border-border/80 bg-card p-5 sm:p-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="flex items-center gap-1.5 rounded-lg bg-primary/10 px-2.5 py-1 text-xs font-semibold text-primary">
                <Cpu className="size-3.5" />
                Autonomous Hunt Engine
              </span>
              <StatusPill status={huntState} />
              {huntData?.mode && (
                <span className="rounded-md border border-border/80 bg-muted/50 px-2 py-0.5 text-xs font-medium text-muted-foreground">
                  {modeLabel[huntData.mode]}
                </span>
              )}
            </div>

            <h2 className="text-xl font-bold tracking-tight text-foreground sm:text-2xl">
              {isHuntActive
                ? huntData?.current_job_title
                  ? `${stageLabel[currentStage]}: ${huntData.current_job_title}${huntData.current_company ? ` at ${huntData.current_company}` : ""}`
                  : stageLabel[currentStage]
                : "Looking for all Software Development & AI Engineering Positions"}
            </h2>

            <p className="max-w-2xl text-xs text-muted-foreground sm:text-sm">
              Actively targeting Frontend, Backend Systems, Full-Stack Engineering, and AI/ML Development across LinkedIn, Greenhouse, and Lever job boards.
            </p>

            {huntData?.last_error && (
              <p className="rounded-lg bg-destructive/10 px-3 py-1.5 text-xs font-medium text-destructive">
                Last error: {huntData.last_error}
              </p>
            )}
          </div>

          {/* Action buttons */}
          <div className="flex flex-wrap items-center gap-2">
            {!isHuntActive ? (
              <Button
                className="h-10 gap-2 rounded-xl px-5 font-semibold"
                onClick={() => handleStartHunt(selectedTrack)}
                disabled={startHunt.isPending}
              >
                <Play className="size-4 fill-white" />
                {startHunt.isPending ? "Starting..." : `Start Hunt (${ROLE_TRACKS[selectedTrack].shortLabel})`}
              </Button>
            ) : (
              <>
                <Button
                  variant="outline"
                  className="h-10 gap-2 rounded-xl border-border/80 bg-card/60 px-4"
                  onClick={handlePauseResume}
                >
                  {isHuntPaused ? <CirclePlay className="size-4 text-emerald-500" /> : <CirclePause className="size-4 text-amber-500" />}
                  {isHuntPaused ? "Resume Hunt" : "Pause"}
                </Button>
                <Button
                  variant="outline"
                  className="h-10 gap-2 rounded-xl border-destructive/30 bg-destructive/5 px-4 text-destructive hover:bg-destructive/10"
                  onClick={handleStop}
                >
                  <Square className="size-4" />
                  Stop
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Target Tracks Selector Pills */}
        <div className="mt-5 border-t border-border/60 pt-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Select Track Focus:
            </span>
            <div className="flex flex-wrap items-center gap-1.5">
              {TRACK_LIST.map((track) => {
                const isSelected = selectedTrack === track.id
                return (
                  <button
                    key={track.id}
                    type="button"
                    onClick={() => setSelectedTrack(track.id)}
                    className={cn(
                      "flex items-center gap-1.5 rounded-xl px-3 py-1.5 text-xs font-semibold transition-all duration-150",
                      isSelected
                        ? "bg-primary text-primary-foreground shadow-sm shadow-primary/25 scale-[1.02]"
                        : "border border-border/80 bg-card/60 text-muted-foreground hover:border-primary/40 hover:text-foreground"
                    )}
                  >
                    <span>{track.badge}</span>
                    <span className="ml-1 rounded-full bg-black/10 px-1.5 py-0.2 text-[10px] dark:bg-white/10">
                      {trackCounts[track.id]}
                    </span>
                  </button>
                )
              })}
            </div>
          </div>
        </div>

        {/* Pipeline Stage Tracker */}
        {isHuntActive && (
          <div className="mt-5 rounded-xl border border-border/60 bg-muted/30 p-3.5">
            <div className="mb-2 flex items-center justify-between text-xs font-medium">
              <span className="text-muted-foreground">Live Pipeline Progress:</span>
              <span className="font-semibold text-primary">{stageLabel[currentStage]}</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5 sm:grid-cols-8">
              {pipelineSteps.map((step, idx) => {
                const activeIndex = pipelineSteps.indexOf(currentStage)
                const isPassed = activeIndex > idx
                const isCurrent = currentStage === step

                return (
                  <div
                    key={step}
                    className={cn(
                      "flex flex-col items-center rounded-lg p-1.5 text-center text-[10px] font-medium transition-all",
                      isCurrent && "bg-primary text-primary-foreground font-semibold shadow-xs animate-pulse",
                      isPassed && "bg-primary/15 text-primary",
                      !isCurrent && !isPassed && "bg-muted/60 text-muted-foreground"
                    )}
                    title={stageLabel[step]}
                  >
                    <span className="truncate w-full">{step}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* Metric Counters */}
        <dl className="mt-5 grid grid-cols-2 gap-px overflow-hidden rounded-xl border border-border/80 bg-border/60 sm:grid-cols-5">
          {counters.map((counter) => (
            <div key={counter.label} className="bg-card/90 px-4 py-3 backdrop-blur-xs transition-colors hover:bg-card">
              <dt className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <counter.icon className="size-3 text-muted-foreground/80" />
                <span className="truncate">{counter.label}</span>
              </dt>
              <dd className="mt-1 text-xl font-bold tracking-tight text-foreground tabular">
                {counter.value}
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Data Grid: High-level KPI Cards */}
      <section className="data-grid">
        {/* Daily Quota Card */}
        <div className="panel p-4 sm:p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Submitted Today
            </p>
            <div className="rounded-lg bg-primary/10 p-1.5 text-primary">
              <Send className="size-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-2xl font-bold tracking-tight text-foreground tabular">
              {submittedToday}
            </p>
            <span className="text-xs text-muted-foreground">/ {dailyLimit} daily limit</span>
          </div>
          <div
            className="mt-3 h-2 overflow-hidden rounded-full bg-muted"
            role="progressbar"
            aria-label="Daily application limit used"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={quotaPct}
          >
            <div
              className="h-full rounded-full bg-primary transition-all duration-500"
              style={{ width: `${quotaPct}%` }}
            />
          </div>
          <p className="mt-2 text-right text-[11px] font-medium text-muted-foreground">
            {quotaPct}% quota utilized
          </p>
        </div>

        {/* Pending Review Card */}
        <div className="panel p-4 sm:p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Needs Review
            </p>
            <div className="rounded-lg bg-amber-500/10 p-1.5 text-amber-500">
              <ClipboardCheck className="size-4" />
            </div>
          </div>
          <p className="text-2xl font-bold tracking-tight text-foreground tabular">
            {pending.length}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {pending.length ? "Applications awaiting human review" : "Queue is clear"}
          </p>
        </div>

        {/* Ingested Today */}
        <div className="panel p-4 sm:p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Jobs Found Today
            </p>
            <div className="rounded-lg bg-info/10 p-1.5 text-info">
              <BriefcaseBusiness className="size-4" />
            </div>
          </div>
          <p className="text-2xl font-bold tracking-tight text-foreground tabular">
            {analytics.data?.jobs_ingested_today ?? 0}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {analytics.data?.total_jobs ?? 0} total jobs in database
          </p>
        </div>

        {/* Total Applications All Time */}
        <div className="panel p-4 sm:p-5">
          <div className="mb-3 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Total Applications
            </p>
            <div className="rounded-lg bg-emerald-500/10 p-1.5 text-emerald-500">
              <Inbox className="size-4" />
            </div>
          </div>
          <p className="text-2xl font-bold tracking-tight text-foreground tabular">
            {analytics.data?.total_applications ?? 0}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">All time submissions & drafts</p>
        </div>
      </section>

      {/* Main Content Grid: Review Queue & Analytics */}
      <div className="grid gap-6 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          {/* Applications Needing Review */}
          <Section
            title="Applications Needing Your Review"
            action={
              <Link
                href="/review-queue"
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
              >
                Open Review Queue <ArrowRight className="size-3" />
              </Link>
            }
          >
            {pending.length === 0 ? (
              <EmptyState
                icon={<ClipboardCheck className="size-5" />}
                title="All caught up!"
                hint="Prepared applications pause here before sending so you can review tailored resumes and answers."
              />
            ) : (
              <ul className="-my-2 divide-y divide-border/60">
                {pending.slice(0, 5).map((item) => (
                  <li key={item.id} className="flex items-center justify-between gap-3 py-3.5">
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-semibold text-foreground">{item.role}</p>
                      <p className="truncate text-xs text-muted-foreground">{item.company}</p>
                    </div>
                    {item.confidence != null && (
                      <ScoreBadge score={item.confidence} label="match" className="hidden sm:inline-flex" />
                    )}
                    <div className="flex items-center gap-2">
                      <Button
                        size="sm"
                        className="rounded-lg bg-primary px-3 text-xs text-primary-foreground shadow-xs hover:opacity-90"
                        onClick={() => handleApprove(item.id)}
                        disabled={approve.isPending}
                      >
                        Approve
                      </Button>
                      <Link
                        href={`/review-queue`}
                        className={cn(
                          buttonVariants({ variant: "outline", size: "sm" }),
                          "rounded-lg px-2.5 text-xs text-muted-foreground"
                        )}
                      >
                        Inspect
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {/* Recent Applications Table */}
          <Section
            title="Recent Applications"
            action={
              <Link
                href="/jobs"
                className="inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline"
              >
                View all jobs <ArrowRight className="size-3" />
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
              <div className="-mx-5 -my-5 overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border/80 text-left text-xs text-muted-foreground">
                      <th className="px-5 py-3 font-semibold">Role & Company</th>
                      <th className="px-5 py-3 font-semibold">Status</th>
                      <th className="hidden px-5 py-3 font-semibold sm:table-cell">Mode</th>
                      <th className="px-5 py-3 text-right font-semibold">Date</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/60">
                    {recent.map((application) => (
                      <tr key={application.id} className="transition-colors hover:bg-muted/40">
                        <td className="max-w-[16rem] px-5 py-3.5">
                          <Link
                            href={`/jobs/${application.job_id}`}
                            className="block truncate font-semibold text-foreground hover:text-primary"
                          >
                            {application.job_title ?? `Job #${application.job_id}`}
                          </Link>
                        </td>
                        <td className="px-5 py-3.5">
                          <StatusPill status={application.status} />
                        </td>
                        <td className="hidden px-5 py-3.5 text-xs text-muted-foreground capitalize sm:table-cell">
                          {application.mode.replaceAll("_", " ")}
                        </td>
                        <td className="px-5 py-3.5 text-right text-xs text-muted-foreground whitespace-nowrap">
                          {formatRelative(application.created_at)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Section>

          {/* Discovery & Application Trends Chart */}
          <Section title="14-Day Activity Trends">
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
                    borderRadius: 10,
                    fontSize: 12,
                    boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="jobs" name="Jobs Found" fill="var(--color-chart-2)" radius={[4, 4, 0, 0]} />
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

        {/* Sidebar Column: Activity & System Diagnostics */}
        <div className="space-y-6">
          {/* Target Track Distribution Card */}
          <Section title="Target Role Breakdown">
            <div className="space-y-3">
              <p className="text-xs text-muted-foreground">
                Distribution of discovered positions matching your target tracks:
              </p>
              <div className="space-y-2">
                {TRACK_LIST.filter((t) => t.id !== "all").map((track) => {
                  const count = trackCounts[track.id]
                  const total = allJobs.data?.length || 1
                  const pct = Math.round((count / total) * 100)
                  return (
                    <div key={track.id} className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-medium text-foreground">{track.badge}</span>
                        <span className="font-mono text-muted-foreground">
                          {count} roles ({pct}%)
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                        <div
                          className="h-full rounded-full bg-primary/80 transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </Section>

          {/* Live Activity Feed */}
          <Section title="System Events">
            {(activity.data ?? []).length === 0 ? (
              <EmptyState
                icon={<Inbox className="size-5" />}
                title="No events yet"
                hint="Discovery, scoring, and application events stream here in real time."
              />
            ) : (
              <ol className="relative space-y-4 border-l border-border/80 pl-5">
                {(activity.data ?? []).slice(0, 7).map((entry) => (
                  <li key={`${entry.timestamp}-${entry.title}`} className="relative">
                    <span className="absolute -left-[25px] top-1.5 size-2 rounded-full bg-primary ring-4 ring-background" />
                    <p className="text-xs font-semibold leading-snug text-foreground">{entry.title}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">
                      {formatRelative(entry.timestamp)}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </Section>

          {/* Diagnostics Card */}
          <Section title="Service Health">
            <ul className="space-y-3">
              {health.map((item) => (
                <li key={item.label} className="flex items-center justify-between gap-3 text-xs">
                  <span className="text-muted-foreground">{item.label}</span>
                  <span className="inline-flex items-center gap-1.5 font-medium">
                    <span
                      className={cn("size-2 rounded-full", item.ok ? "bg-emerald-500" : "bg-amber-500")}
                      aria-hidden="true"
                    />
                    <span className={item.ok ? "text-foreground" : "text-amber-500"}>
                      {item.ok ? item.okText : item.badText}
                    </span>
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
