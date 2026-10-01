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
import { ArrowUpDown, ExternalLink, FileText, PlayCircle, Search, Sparkles } from "lucide-react"
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
import { useJobs, useJobWorkspace } from "@/hooks/use-console-queries"
import { useUiStore } from "@/stores/ui-store"
import type { JobSummary } from "@/types/api"
import { formatRelative } from "@/utils/format"

export function JobsExplorerPage() {
  const selectedJobId = useUiStore((state) => state.selectedJobId)
  const setSelectedJobId = useUiStore((state) => state.setSelectedJobId)
  const [search, setSearch] = useState("")
  const [atsFilter, setAtsFilter] = useState<string>("all")
  const [minScore, setMinScore] = useState<number>(0)
  const [sorting, setSorting] = useState<SortingState>([
    {
      id: "created_at",
      desc: true,
    },
  ])

  const jobsQuery = useJobs({ limit: 300 })
  const workspaceQuery = useJobWorkspace(selectedJobId ?? Number.NaN)

  const data = useMemo(() => {
    const jobs = jobsQuery.data ?? []
    return jobs.filter((job) => {
      const text = `${job.title} ${job.company} ${job.location ?? ""}`.toLowerCase()
      if (search && !text.includes(search.toLowerCase())) return false
      if (atsFilter !== "all" && job.ats_source !== atsFilter) return false
      if ((job.latest_score ?? 0) < minScore) return false
      return true
    })
  }, [atsFilter, jobsQuery.data, minScore, search])

  const columns = useMemo<ColumnDef<JobSummary>[]>(
    () => [
      {
        accessorKey: "title",
        header: "Role",
        cell: ({ row }) => (
          <div className="min-w-0">
            <p className="truncate font-medium">{row.original.title}</p>
            <p className="truncate text-xs text-muted-foreground">{row.original.company}</p>
          </div>
        ),
      },
      {
        accessorKey: "location",
        header: "Location",
        cell: ({ row }) => (
          <span className="text-xs text-muted-foreground">{row.original.location ?? "n/a"}</span>
        ),
      },
      {
        accessorKey: "latest_score",
        header: "Score",
        cell: ({ row }) => <ScoreBadge score={row.original.latest_score} label="fit" />,
      },
      {
        accessorKey: "ats_source",
        header: "ATS",
        cell: ({ row }) => <span className="text-xs uppercase">{row.original.ats_source}</span>,
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
            className="-ml-2"
          >
            Created
            <ArrowUpDown className="ml-1 size-3" />
          </Button>
        ),
        cell: ({ row }) => (
          <span className="text-xs text-muted-foreground">{formatRelative(row.original.created_at)}</span>
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
      <PageHeader
        title="Jobs Explorer"
        description="Filter jobs by score, source, ATS, and status. Select a row to inspect a full workflow panel."
      />

      <div className="panel p-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative w-72 max-w-full">
            <Search className="pointer-events-none absolute left-2 top-2.5 size-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search role/company/location..."
              className="pl-8"
            />
          </div>
          <Select
            value={atsFilter}
            onValueChange={(value) => setAtsFilter(value ?? "all")}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="ATS source" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All ATS</SelectItem>
              <SelectItem value="greenhouse">Greenhouse</SelectItem>
              <SelectItem value="lever">Lever</SelectItem>
              <SelectItem value="linkedin">LinkedIn</SelectItem>
              <SelectItem value="generic">Generic</SelectItem>
            </SelectContent>
          </Select>
          <Select
            value={String(minScore)}
            onValueChange={(value) => setMinScore(Number(value))}
          >
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Min score" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="0">Any score</SelectItem>
              <SelectItem value="0.4">40%+</SelectItem>
              <SelectItem value="0.6">60%+</SelectItem>
              <SelectItem value="0.8">80%+</SelectItem>
            </SelectContent>
          </Select>
          <div className="ml-auto text-xs text-muted-foreground">{data.length} jobs</div>
        </div>
      </div>

      <Group orientation="horizontal" className="min-h-[68vh] gap-2">
        <Panel defaultSize={70} minSize={45}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Ingested Jobs</CardTitle>
            </CardHeader>
            <CardContent className="h-[calc(68vh-4rem)] p-0">
              <ScrollArea className="h-full">
                <Table>
                  <TableHeader>
                    {table.getHeaderGroups().map((headerGroup) => (
                      <TableRow key={headerGroup.id}>
                        {headerGroup.headers.map((header) => (
                          <TableHead key={header.id}>
                            {header.isPlaceholder
                              ? null
                              : flexRender(
                                  header.column.columnDef.header,
                                  header.getContext()
                                )}
                          </TableHead>
                        ))}
                      </TableRow>
                    ))}
                  </TableHeader>
                  <TableBody>
                    {table.getRowModel().rows.map((row) => (
                      <TableRow
                        key={row.id}
                        className="cursor-pointer"
                        data-state={
                          selectedJobId === row.original.id ? "selected" : undefined
                        }
                        onClick={() => setSelectedJobId(row.original.id)}
                      >
                        {row.getVisibleCells().map((cell) => (
                          <TableCell key={cell.id}>
                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            </CardContent>
          </Card>
        </Panel>

        <Separator className="w-2 rounded-full bg-border/50 hover:bg-primary/50" />

        <Panel defaultSize={30} minSize={20}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Job Inspector</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {!selectedJobId ? (
                <p className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
                  Select a job row to inspect details and execute workflow actions.
                </p>
              ) : workspaceQuery.isLoading ? (
                <p className="text-sm text-muted-foreground">Loading workspace...</p>
              ) : workspaceQuery.data ? (
                <>
                  <div>
                    <p className="text-base font-semibold">{workspaceQuery.data.job.title}</p>
                    <p className="text-xs text-muted-foreground">
                      {workspaceQuery.data.job.company} · {workspaceQuery.data.job.location ?? "n/a"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <StatusPill status={workspaceQuery.data.job.status} />
                    <ScoreBadge
                      score={workspaceQuery.data.latest_score?.composite}
                      label="composite"
                    />
                  </div>
                  <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-2">
                    <div className="rounded-lg border border-border/70 p-2">
                      resumes: {workspaceQuery.data.resume_versions.length}
                    </div>
                    <div className="rounded-lg border border-border/70 p-2">
                      applications: {workspaceQuery.data.applications.length}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      Actions
                    </h4>
                    <div className="grid gap-2">
                      <Link href={`/jobs/${workspaceQuery.data.job.id}`}>
                        <Button variant="default" className="w-full justify-start">
                          <Sparkles className="mr-2 size-4" />
                          Open Job Detail
                        </Button>
                      </Link>
                      <Link href="/resume-studio">
                        <Button variant="outline" className="w-full justify-start">
                          <FileText className="mr-2 size-4" />
                          Resume Studio
                        </Button>
                      </Link>
                      <Link href="/live-browser">
                        <Button variant="outline" className="w-full justify-start">
                          <PlayCircle className="mr-2 size-4" />
                          Automation Monitor
                        </Button>
                      </Link>
                      <Link href={workspaceQuery.data.job.source_url} target="_blank">
                        <Button variant="ghost" className="w-full justify-start">
                          <ExternalLink className="mr-2 size-4" />
                          Open Source Posting
                        </Button>
                      </Link>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted-foreground">Failed to load workspace data.</p>
              )}
            </CardContent>
          </Card>
        </Panel>
      </Group>
    </div>
  )
}
