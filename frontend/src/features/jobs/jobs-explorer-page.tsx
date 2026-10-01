"use client"

import { useMemo, useState } from "react"
import Link from "next/link"
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table"
import {
  ArrowUpDown,
  BriefcaseBusiness,
  Building2,
  ExternalLink,
  FileText,
  Filter,
  Grid3X3,
  List,
  MapPin,
  PlayCircle,
  Search,
  Sparkles,
  X,
} from "lucide-react"
import { Group, Panel, Separator } from "react-resizable-panels"

import { PageHeader } from "@/components/layout/page-header"
import { ScoreBadge } from "@/components/workflow/score-badge"
import { StatusPill } from "@/components/workflow/status-pill"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  ROLE_TRACKS,
  TRACK_LIST,
  RoleTrackId,
  identifyJobTracks,
  matchesTrack,
} from "@/features/jobs/role-tracks"
import { useJobs, useJobWorkspace } from "@/hooks/use-console-queries"
import { cn } from "@/lib/utils"
import { useUiStore } from "@/stores/ui-store"
import type { JobSummary } from "@/types/api"
import { formatRelative } from "@/utils/format"

export function JobsExplorerPage() {
  const selectedJobId = useUiStore((state) => state.selectedJobId)
  const setSelectedJobId = useUiStore((state) => state.setSelectedJobId)
  const [search, setSearch] = useState("")
  const [atsFilter, setAtsFilter] = useState<string>("all")
  const [minScore, setMinScore] = useState<number>(0)
  const [selectedTrack, setSelectedTrack] = useState<RoleTrackId>("all")
  const [viewMode, setViewMode] = useState<"table" | "grid">("table")
  const [sorting, setSorting] = useState<SortingState>([
    {
      id: "created_at",
      desc: true,
    },
  ])

  const jobsQuery = useJobs({ limit: 400 })
  const workspaceQuery = useJobWorkspace(selectedJobId ?? Number.NaN)

  // Track counts across all jobs
  const trackCounts = useMemo(() => {
    const counts: Record<RoleTrackId, number> = {
      all: jobsQuery.data?.length ?? 0,
      frontend: 0,
      backend: 0,
      fullstack: 0,
      ai: 0,
    }
    for (const job of jobsQuery.data ?? []) {
      const tracks = identifyJobTracks(job)
      for (const t of tracks) {
        counts[t] = (counts[t] || 0) + 1
      }
    }
    return counts
  }, [jobsQuery.data])

  const data = useMemo(() => {
    const jobs = jobsQuery.data ?? []
    return jobs.filter((job) => {
      // Track filter
      if (!matchesTrack(job, selectedTrack)) return false

      // Text search
      const text = `${job.title} ${job.company} ${job.location ?? ""}`.toLowerCase()
      if (search && !text.includes(search.toLowerCase())) return false

      // ATS filter
      if (atsFilter !== "all" && job.ats_source !== atsFilter) return false

      // Minimum score
      if ((job.latest_score ?? 0) < minScore) return false

      return true
    })
  }, [atsFilter, jobsQuery.data, minScore, search, selectedTrack])

  const columns = useMemo<ColumnDef<JobSummary>[]>(
    () => [
      {
        accessorKey: "title",
        header: "Role & Track",
        cell: ({ row }) => {
          const tracks = identifyJobTracks(row.original)
          return (
            <div className="min-w-0 space-y-1">
              <p className="truncate font-semibold text-foreground">{row.original.title}</p>
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="truncate text-xs text-muted-foreground">{row.original.company}</span>
                {tracks.slice(0, 2).map((t) => (
                  <span
                    key={t}
                    className={cn(
                      "rounded-md px-1.5 py-0.2 text-[10px] font-medium",
                      ROLE_TRACKS[t].bgTone,
                      ROLE_TRACKS[t].textTone
                    )}
                  >
                    {ROLE_TRACKS[t].shortLabel}
                  </span>
                ))}
              </div>
            </div>
          )
        },
      },
      {
        accessorKey: "location",
        header: "Location",
        cell: ({ row }) => (
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <MapPin className="size-3 shrink-0" />
            <span className="truncate">{row.original.location ?? "Remote / Unspecified"}</span>
          </div>
        ),
      },
      {
        accessorKey: "latest_score",
        header: ({ column }) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-2 text-xs font-semibold"
          >
            Fit Score
            <ArrowUpDown className="ml-1 size-3" />
          </Button>
        ),
        cell: ({ row }) => <ScoreBadge score={row.original.latest_score} label="fit" />,
      },
      {
        accessorKey: "ats_source",
        header: "Source",
        cell: ({ row }) => (
          <span className="rounded-md border border-border/80 bg-muted/40 px-2 py-0.5 text-[11px] font-mono uppercase text-muted-foreground">
            {row.original.ats_source}
          </span>
        ),
      },
      {
        accessorKey: "status",
        header: "Status",
        cell: ({ row }) => <StatusPill status={row.original.status} />,
      },
      {
        accessorKey: "created_at",
        header: ({ column }) => (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
            className="-ml-2 text-xs font-semibold"
          >
            Discovered
            <ArrowUpDown className="ml-1 size-3" />
          </Button>
        ),
        cell: ({ row }) => (
          <span className="text-xs text-muted-foreground whitespace-nowrap">
            {formatRelative(row.original.created_at)}
          </span>
        ),
      },
    ],
    []
  )

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  })

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <PageHeader
          title="Jobs Explorer"
          description="Filter openings by engineering discipline, ATS, and AI fit score. Inspect and tailor applications."
        />
        <div className="flex items-center gap-1 rounded-xl border border-border/80 bg-card/60 p-1 shadow-xs">
          <Button
            variant={viewMode === "table" ? "secondary" : "ghost"}
            size="sm"
            className="h-8 gap-1.5 rounded-lg px-2.5 text-xs font-medium"
            onClick={() => setViewMode("table")}
          >
            <List className="size-3.5" />
            Table
          </Button>
          <Button
            variant={viewMode === "grid" ? "secondary" : "ghost"}
            size="sm"
            className="h-8 gap-1.5 rounded-lg px-2.5 text-xs font-medium"
            onClick={() => setViewMode("grid")}
          >
            <Grid3X3 className="size-3.5" />
            Grid
          </Button>
        </div>
      </div>

      {/* Target Track Filter Chips */}
      <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border/80 bg-card/60 p-2.5 shadow-xs backdrop-blur-md">
        <span className="ml-1 flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Filter className="size-3" />
          Tracks:
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
                    ? "bg-primary text-primary-foreground shadow-xs shadow-primary/25 scale-[1.02]"
                    : "border border-border/70 bg-card/80 text-muted-foreground hover:border-primary/40 hover:text-foreground"
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

      {/* Search and Secondary Filter Bar */}
      <div className="panel p-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <div className="relative min-w-[240px] flex-1 max-w-md">
            <Search className="pointer-events-none absolute left-3 top-2.5 size-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search title, company, skills, or location..."
              className="rounded-xl pl-9 pr-8"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch("")}
                className="absolute right-2.5 top-2.5 text-muted-foreground hover:text-foreground"
              >
                <X className="size-4" />
              </button>
            )}
          </div>

          <Select value={atsFilter} onValueChange={(value) => setAtsFilter(value ?? "all")}>
            <SelectTrigger className="w-36 rounded-xl">
              <SelectValue placeholder="ATS source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Sources</SelectItem>
              <SelectItem value="greenhouse">Greenhouse</SelectItem>
              <SelectItem value="lever">Lever</SelectItem>
              <SelectItem value="linkedin">LinkedIn</SelectItem>
              <SelectItem value="generic">Generic</SelectItem>
            </SelectContent>
          </Select>

          <Select value={String(minScore)} onValueChange={(value) => setMinScore(Number(value))}>
            <SelectTrigger className="w-36 rounded-xl">
              <SelectValue placeholder="Min score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Any Fit Score</SelectItem>
              <SelectItem value="0.4">40%+ Fit</SelectItem>
              <SelectItem value="0.6">60%+ Fit (Recommended)</SelectItem>
              <SelectItem value="0.8">80%+ Strong Fit</SelectItem>
            </SelectContent>
          </Select>

          <div className="ml-auto text-xs font-semibold text-muted-foreground">
            Showing <span className="text-foreground font-bold">{data.length}</span> matching openings
          </div>
        </div>
      </div>

      {/* Split View: List/Grid + Job Inspector Pane */}
      <Group orientation="horizontal" className="min-h-[70vh] gap-3">
        <Panel defaultSize={68} minSize={45}>
          <Card className="h-full rounded-2xl border-border/80 bg-card/60 shadow-xs backdrop-blur-md">
            <CardHeader className="flex flex-row items-center justify-between border-b border-border/80 px-4 py-3">
              <CardTitle className="text-sm font-semibold">
                {ROLE_TRACKS[selectedTrack].label} Postings ({data.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(70vh-3.5rem)] p-0">
              <ScrollArea className="h-full">
                {data.length === 0 ? (
                  <div className="flex flex-col items-center justify-center p-12 text-center">
                    <div className="rounded-full bg-muted p-3 text-muted-foreground">
                      <BriefcaseBusiness className="size-6" />
                    </div>
                    <p className="mt-3 text-sm font-semibold">No jobs match this filter</p>
                    <p className="mt-1 text-xs text-muted-foreground max-w-xs">
                      Try selecting "All Roles" or clearing your search term to see more positions.
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      className="mt-4 rounded-xl"
                      onClick={() => {
                        setSelectedTrack("all")
                        setSearch("")
                        setAtsFilter("all")
                        setMinScore(0)
                      }}
                    >
                      Reset All Filters
                    </Button>
                  </div>
                ) : viewMode === "table" ? (
                  <Table>
                    <TableHeader>
                      {table.getHeaderGroups().map((headerGroup) => (
                        <TableRow key={headerGroup.id} className="border-border/80 bg-muted/20">
                          {headerGroup.headers.map((header) => (
                            <TableHead key={header.id} className="px-4 py-3 text-xs font-semibold">
                              {header.isPlaceholder
                                ? null
                                : flexRender(header.column.columnDef.header, header.getContext())}
                            </TableHead>
                          ))}
                        </TableRow>
                      ))}
                    </TableHeader>
                    <TableBody>
                      {table.getRowModel().rows.map((row) => {
                        const isSelected = selectedJobId === row.original.id
                        return (
                          <TableRow
                            key={row.id}
                            className={cn(
                              "cursor-pointer border-border/60 transition-colors",
                              isSelected
                                ? "bg-primary/10 hover:bg-primary/15"
                                : "hover:bg-muted/40"
                            )}
                            data-state={isSelected ? "selected" : undefined}
                            onClick={() => setSelectedJobId(row.original.id)}
                          >
                            {row.getVisibleCells().map((cell) => (
                              <TableCell key={cell.id} className="px-4 py-3">
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                              </TableCell>
                            ))}
                          </TableRow>
                        )
                      })}
                    </TableBody>
                  </Table>
                ) : (
                  /* Grid Card View */
                  <div className="grid gap-3 p-4 sm:grid-cols-2">
                    {data.map((job) => {
                      const isSelected = selectedJobId === job.id
                      const tracks = identifyJobTracks(job)

                      return (
                        <div
                          key={job.id}
                          onClick={() => setSelectedJobId(job.id)}
                          className={cn(
                            "cursor-pointer rounded-xl border p-4 transition-all duration-200",
                            isSelected
                              ? "border-primary bg-primary/10 shadow-sm"
                              : "border-border/80 bg-card hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
                          )}
                        >
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0 space-y-1">
                              <p className="truncate font-semibold text-foreground text-sm">
                                {job.title}
                              </p>
                              <p className="truncate text-xs text-muted-foreground flex items-center gap-1">
                                <Building2 className="size-3" />
                                {job.company}
                              </p>
                            </div>
                            <ScoreBadge score={job.latest_score} label="fit" />
                          </div>

                          <div className="mt-3 flex flex-wrap items-center gap-1.5">
                            {tracks.map((t) => (
                              <span
                                key={t}
                                className={cn(
                                  "rounded-md px-1.5 py-0.5 text-[10px] font-semibold",
                                  ROLE_TRACKS[t].bgTone,
                                  ROLE_TRACKS[t].textTone
                                )}
                              >
                                {ROLE_TRACKS[t].badge}
                              </span>
                            ))}
                            <span className="rounded-md border border-border/60 bg-muted/40 px-1.5 py-0.5 text-[10px] font-mono uppercase text-muted-foreground">
                              {job.ats_source}
                            </span>
                          </div>

                          <div className="mt-3 flex items-center justify-between border-t border-border/60 pt-2.5 text-[11px] text-muted-foreground">
                            <span className="truncate flex items-center gap-1">
                              <MapPin className="size-3" />
                              {job.location ?? "Remote"}
                            </span>
                            <span>{formatRelative(job.created_at)}</span>
                          </div>
                        </div>
                      )
                    })}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </Panel>

        <Separator className="w-2 rounded-full bg-border/50 hover:bg-primary/50 transition-colors" />

        {/* Inspector Panel */}
        <Panel defaultSize={32} minSize={24}>
          <Card className="h-full rounded-2xl border-border/80 bg-card/60 shadow-xs backdrop-blur-md">
            <CardHeader className="border-b border-border/80 px-4 py-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-1.5">
                <Sparkles className="size-4 text-primary" />
                Job & AI Fit Inspector
              </CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(70vh-3.5rem)] p-4">
              <ScrollArea className="h-full pr-2">
                {!selectedJobId ? (
                  <div className="rounded-xl border border-dashed border-border/80 p-8 text-center text-muted-foreground">
                    <BriefcaseBusiness className="mx-auto size-8 opacity-40" />
                    <p className="mt-2 text-sm font-medium">Select a job row or card</p>
                    <p className="mt-1 text-xs">
                      Inspect match breakdown, tailored resume options, and application forms.
                    </p>
                  </div>
                ) : workspaceQuery.isLoading ? (
                  <p className="text-sm text-muted-foreground">Loading workspace details...</p>
                ) : workspaceQuery.data ? (
                  <div className="space-y-4">
                    {/* Job Title & Company */}
                    <div className="space-y-1">
                      <p className="text-base font-bold text-foreground">
                        {workspaceQuery.data.job.title}
                      </p>
                      <p className="text-xs font-medium text-muted-foreground">
                        {workspaceQuery.data.job.company} · {workspaceQuery.data.job.location ?? "Remote (US)"}
                      </p>
                    </div>

                    {/* Matched Tracks */}
                    <div className="flex flex-wrap gap-1.5">
                      {identifyJobTracks(workspaceQuery.data.job).map((t) => (
                        <span
                          key={t}
                          className={cn(
                            "rounded-lg px-2 py-0.5 text-xs font-semibold",
                            ROLE_TRACKS[t].bgTone,
                            ROLE_TRACKS[t].textTone,
                            ROLE_TRACKS[t].borderTone,
                            "border"
                          )}
                        >
                          {ROLE_TRACKS[t].badge}
                        </span>
                      ))}
                    </div>

                    {/* Status & Composite Score */}
                    <div className="flex items-center justify-between rounded-xl border border-border/80 bg-card/90 p-3 shadow-xs">
                      <StatusPill status={workspaceQuery.data.job.status} />
                      <ScoreBadge
                        score={workspaceQuery.data.latest_score?.composite}
                        label="overall match"
                      />
                    </div>

                    {/* AI Scoring Factor Breakdown */}
                    {workspaceQuery.data.latest_score && (
                      <div className="space-y-2 rounded-xl border border-border/80 bg-muted/30 p-3">
                        <p className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                          Match Score Breakdown
                        </p>
                        <div className="space-y-1.5 text-xs">
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Skill Overlap:</span>
                            <span className="font-semibold tabular">
                              {((workspaceQuery.data.latest_score.skill_overlap ?? 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Seniority Fit:</span>
                            <span className="font-semibold tabular">
                              {((workspaceQuery.data.latest_score.seniority_alignment ?? 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Location Alignment:</span>
                            <span className="font-semibold tabular">
                              {((workspaceQuery.data.latest_score.location_compatibility ?? 0) * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Quick Stats Grid */}
                    <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground">
                      <div className="rounded-xl border border-border/80 bg-card p-2.5">
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground/70">
                          Resumes
                        </span>
                        <p className="text-base font-bold text-foreground">
                          {workspaceQuery.data.resume_versions.length}
                        </p>
                      </div>
                      <div className="rounded-xl border border-border/80 bg-card p-2.5">
                        <span className="text-[10px] uppercase font-semibold text-muted-foreground/70">
                          Applications
                        </span>
                        <p className="text-base font-bold text-foreground">
                          {workspaceQuery.data.applications.length}
                        </p>
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div className="space-y-2 pt-2">
                      <h4 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                        Actions
                      </h4>
                      <div className="grid gap-2">
                        <Link href={`/jobs/${workspaceQuery.data.job.id}`}>
                          <Button className="w-full justify-start rounded-xl font-semibold shadow-xs">
                            <Sparkles className="mr-2 size-4" />
                            Open Full Job Workspace
                          </Button>
                        </Link>
                        <Link href="/resume-studio">
                          <Button variant="outline" className="w-full justify-start rounded-xl">
                            <FileText className="mr-2 size-4 text-primary" />
                            Resume Studio
                          </Button>
                        </Link>
                        <Link href="/live-browser">
                          <Button variant="outline" className="w-full justify-start rounded-xl">
                            <PlayCircle className="mr-2 size-4 text-emerald-500" />
                            Automation Session
                          </Button>
                        </Link>
                        <Link href={workspaceQuery.data.job.source_url} target="_blank">
                          <Button variant="ghost" className="w-full justify-start rounded-xl text-muted-foreground">
                            <ExternalLink className="mr-2 size-4" />
                            Original Source Posting
                          </Button>
                        </Link>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Failed to load workspace data.</p>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </Panel>
      </Group>
    </div>
  )
}
