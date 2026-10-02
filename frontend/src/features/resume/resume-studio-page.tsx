"use client"

import { useRef, useMemo, useState } from "react"
import { Group, Panel, Separator } from "react-resizable-panels"
import { ExternalLink, FileText, Upload, CheckCircle2 } from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { ScoreBadge } from "@/components/workflow/score-badge"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  useJobWorkspace,
  useJobs,
  useMasterResumeInfo,
  useResumesForJob,
  useSettings,
  useUpdateSettings,
  useUploadMasterResume,
} from "@/hooks/use-console-queries"
import { apiBaseUrl } from "@/lib/env"
import { useUiStore } from "@/stores/ui-store"
import { formatDateTime } from "@/utils/format"

function toLines(value: unknown): string[] {
  return JSON.stringify(value ?? {}, null, 2).split("\n")
}

export function ResumeStudioPage() {
  const jobs = useJobs({ limit: 200 })
  const settings = useSettings()
  const updateSettings = useUpdateSettings()
  const masterResumeInfo = useMasterResumeInfo()
  const uploadMasterResume = useUploadMasterResume()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isDragging, setIsDragging] = useState(false)
  const rememberedJobId = useUiStore((state) => state.selectedJobId)
  const [selectedJobId, setSelectedJobId] = useState<number | null>(rememberedJobId)
  const resumes = useResumesForJob(selectedJobId ?? Number.NaN)
  const workspace = useJobWorkspace(selectedJobId ?? Number.NaN)

  const masterLines = useMemo(
    () => toLines(settings.data?.resume_master ?? {}),
    [settings.data?.resume_master]
  )

  const latestResume = useMemo(() => resumes.data?.[0] ?? null, [resumes.data])
  const generatedLines = useMemo(
    () =>
      toLines(
        latestResume
          ? {
              id: latestResume.id,
              template: latestResume.template,
              kind: latestResume.kind,
              pdf_path: latestResume.pdf_path,
              docx_path: latestResume.docx_path,
            }
          : {}
      ),
    [latestResume]
  )

  const modifiedLineIndexes = useMemo(() => {
    const set = new Set<number>()
    const max = Math.max(masterLines.length, generatedLines.length)
    for (let i = 0; i < max; i += 1) {
      if (masterLines[i] !== generatedLines[i]) {
        set.add(i)
      }
    }
    return set
  }, [generatedLines, masterLines])

  async function importMasterResume(file: File) {
    try {
      const text = await file.text()
      const parsed = JSON.parse(text) as Record<string, unknown>
      await updateSettings.mutateAsync({
        section: "resume_master",
        data: parsed,
      })
      toast.success("Imported resume_master.json from dropped file")
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown import failure"
      toast.error(`Import failed: ${message}`)
    }
  }

  async function handlePdfUpload(file: File) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      toast.error("Please upload a PDF file")
      return
    }
    try {
      const result = await uploadMasterResume.mutateAsync(file)
      toast.success(`Master resume uploaded (${(result.size_bytes / 1024).toFixed(1)} KB)`)
    } catch (error) {
      const message = error instanceof Error ? error.message : "Upload failed"
      toast.error(message)
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Resume Studio"
        description="Compare master resume content with generated versions, inspect optimization hints, and export paths."
      />

      {/* Master Resume PDF Upload */}
      <Card className="rounded-2xl border-border/70 bg-card/50">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <FileText className="size-4 text-primary" />
            Master Resume PDF
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 sm:grid-cols-[1fr,auto]">
            <div
              className={`relative flex flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed p-6 transition-colors cursor-pointer ${
                isDragging
                  ? "border-primary bg-primary/10"
                  : "border-border/70 hover:border-primary/60 hover:bg-muted/20"
              }`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setIsDragging(false)
                const file = e.dataTransfer.files?.[0]
                if (file) void handlePdfUpload(file)
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) void handlePdfUpload(file)
                  e.target.value = ""
                }}
              />
              <Upload className="size-8 text-muted-foreground" />
              <div className="text-center">
                <p className="text-sm font-medium">
                  {uploadMasterResume.isPending ? "Uploading…" : "Drag & drop your resume PDF here"}
                </p>
                <p className="text-xs text-muted-foreground mt-1">or click to browse · PDF only</p>
              </div>
            </div>

            {/* Current file info */}
            <div className="flex flex-col justify-center gap-2 min-w-[220px] rounded-xl border border-border/70 p-4">
              {masterResumeInfo.data?.exists ? (
                <>
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="size-4 text-emerald-500 shrink-0" />
                    <p className="text-sm font-medium truncate">Resume on file</p>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {masterResumeInfo.data.filename}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {masterResumeInfo.data.size_bytes
                      ? `${(masterResumeInfo.data.size_bytes / 1024).toFixed(1)} KB`
                      : ""}
                  </p>
                  <button
                    type="button"
                    className="mt-1 text-xs text-primary underline underline-offset-2 text-left"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Replace PDF
                  </button>
                </>
              ) : (
                <div className="text-center">
                  <FileText className="mx-auto size-8 text-muted-foreground/40 mb-2" />
                  <p className="text-xs text-muted-foreground">No resume uploaded yet</p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="panel p-3">
        <div className="flex flex-wrap items-center gap-2">
          <Select
            value={selectedJobId ? String(selectedJobId) : "none"}
            onValueChange={(value) => setSelectedJobId(value === "none" ? null : Number(value))}
          >
            <SelectTrigger className="w-96 max-w-full">
              <SelectValue placeholder="Select a job to inspect generated resumes" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">No job selected</SelectItem>
              {jobs.data?.map((job) => (
                <SelectItem key={job.id} value={String(job.id)}>
                  {job.title} @ {job.company}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Badge variant="outline">versions: {resumes.data?.length ?? 0}</Badge>
          <ScoreBadge score={workspace.data?.latest_score?.composite} label="job fit" />
        </div>
      </div>

      <Group orientation="horizontal" className="min-h-[68vh] gap-2">
        <Panel defaultSize={38} minSize={20}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm">Master Resume (source)</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[calc(68vh-4rem)]">
                <pre className="p-3 text-xs leading-5 text-muted-foreground">
                  {masterLines.join("\n")}
                </pre>
              </ScrollArea>
            </CardContent>
          </Card>
        </Panel>
        <Separator className="w-2 rounded-full bg-border/50 hover:bg-primary/50" />
        <Panel defaultSize={38} minSize={20}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm">Generated Resume Snapshot</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[calc(68vh-4rem)]">
                <pre className="p-3 text-xs leading-5">
                  {generatedLines.map((line, index) => (
                    <div
                      key={`${index}-${line}`}
                      className={
                        modifiedLineIndexes.has(index)
                          ? "rounded bg-emerald-500/10 text-emerald-200"
                          : "text-muted-foreground"
                      }
                    >
                      {line}
                    </div>
                  ))}
                </pre>
              </ScrollArea>
            </CardContent>
          </Card>
        </Panel>
        <Separator className="w-2 rounded-full bg-border/50 hover:bg-primary/50" />
        <Panel defaultSize={24} minSize={18}>
          <Card className="h-full rounded-2xl border-border/70 bg-card/50">
            <CardHeader>
              <CardTitle className="text-sm">Optimization + Assets</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-muted-foreground">
              {workspace.data?.extracted_keywords?.length ? (
                <>
                  <p className="text-xs font-semibold uppercase tracking-wide">Target keywords</p>
                  <div className="flex flex-wrap gap-1.5">
                    {workspace.data.extracted_keywords.slice(0, 24).map((keyword) => (
                      <Badge key={keyword} variant="outline" className="text-[11px]">
                        {keyword}
                      </Badge>
                    ))}
                  </div>
                </>
              ) : (
                <p>No keyword extraction data yet.</p>
              )}

              <div className="space-y-2">
                <p className="text-xs font-semibold uppercase tracking-wide">Version history</p>
                {resumes.data?.map((resume) => (
                  <div key={resume.id} className="rounded-lg border border-border/70 p-2 text-xs">
                    <p className="font-medium">
                      #{resume.id} · {resume.template}
                    </p>
                    <p>kind: {resume.kind}</p>
                    <p>created: {formatDateTime(resume.created_at)}</p>
                    <p className="truncate">pdf: {resume.pdf_path ?? "n/a"}</p>
                  </div>
                ))}
              </div>

              <div
                className="rounded-lg border border-dashed border-border/80 p-3 text-xs text-muted-foreground"
                onDragOver={(event) => {
                  event.preventDefault()
                }}
                onDrop={(event) => {
                  event.preventDefault()
                  const file = event.dataTransfer.files?.[0]
                  if (file) {
                    void importMasterResume(file)
                  }
                }}
              >
                <p className="font-medium text-foreground">Drag and drop resume JSON</p>
                <p className="mt-1">Drop a `resume_master.json` file here to import and validate.</p>
              </div>

              {latestResume ? (
                <div className="space-y-2 rounded-lg border border-border/70 p-3">
                  <p className="text-xs font-semibold uppercase tracking-wide">Export controls</p>
                  <div className="flex flex-wrap gap-2">
                    <a
                      href={`${apiBaseUrl}/resumes/${latestResume.id}/download/pdf`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Button variant="outline" size="sm">
                        PDF
                        <ExternalLink className="ml-2 size-3.5" />
                      </Button>
                    </a>
                    <a
                      href={`${apiBaseUrl}/resumes/${latestResume.id}/download/docx`}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Button variant="outline" size="sm">
                        DOCX
                        <ExternalLink className="ml-2 size-3.5" />
                      </Button>
                    </a>
                  </div>
                </div>
              ) : null}

              <div className="space-y-2 rounded-lg border border-border/70 p-3">
                <p className="text-xs font-semibold uppercase tracking-wide">Cover letter preview</p>
                <p className="max-h-44 overflow-auto whitespace-pre-wrap text-xs text-muted-foreground">
                  {workspace.data?.applications?.find((application) => application.cover_letter)
                    ?.cover_letter ?? "No cover letter captured in application records yet."}
                </p>
              </div>
            </CardContent>
          </Card>
        </Panel>
      </Group>
    </div>
  )
}
