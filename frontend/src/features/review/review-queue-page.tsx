"use client"

import { useMemo, useState } from "react"
import { CheckCircle2, XCircle } from "lucide-react"
import { toast } from "sonner"

import { PageHeader } from "@/components/layout/page-header"
import { StatusPill } from "@/components/workflow/status-pill"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import {
  useApplicationDetail,
  useApplications,
  useApproveCheckpoint,
  useAutomationOverview,
  usePendingApprovals,
  useRejectCheckpoint,
} from "@/hooks/use-console-queries"
import { api } from "@/services/api/endpoints"
import { formatDateTime } from "@/utils/format"

export function ReviewQueuePage() {
  const approvals = usePendingApprovals()
  const applications = useApplications({ status: "awaiting_review", limit: 200 })
  const [selectedCheckpointId, setSelectedCheckpointId] = useState<number | null>(null)
  const approveCheckpoint = useApproveCheckpoint()
  const rejectCheckpoint = useRejectCheckpoint()
  const [notes, setNotes] = useState("")
  const screenshots = useAutomationOverview()

  const selectedApproval = useMemo(() => {
    if (selectedCheckpointId != null) {
      return approvals.data?.find((a) => a.id === selectedCheckpointId)
    }
    return approvals.data?.[0]
  }, [approvals.data, selectedCheckpointId])

  const currentId = selectedApproval?.application_id ?? null

  const detail = useApplicationDetail(currentId ?? Number.NaN)

  const handleApprove = async () => {
    if (!selectedApproval) return
    const assistOnly = Boolean(selectedApproval.payload?.assist_only)
    await approveCheckpoint.mutateAsync({
      id: selectedApproval.id,
      submit: !assistOnly,
    })
    toast.success(
      assistOnly
        ? "Approved — complete submission manually in Firefox"
        : `Checkpoint #${selectedApproval.id} approved`
    )
  }

  const handleReject = async () => {
    if (!selectedApproval) return
    await rejectCheckpoint.mutateAsync(selectedApproval.id)
    toast.warning(`Checkpoint #${selectedApproval.id} rejected`)
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Application Review Queue"
        description="Moderation-style workflow for human approval before final submission."
      />
      <div className="grid gap-4 xl:grid-cols-[360px,1fr]">
        <Card className="rounded-2xl border-border/70 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">Pending Applications</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[70vh]">
              <div className="space-y-2 p-3">
                {approvals.data?.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    onClick={() => setSelectedCheckpointId(item.id)}
                    className={`w-full rounded-xl border p-3 text-left transition ${
                      selectedApproval?.id === item.id
                        ? "border-primary/60 bg-primary/10"
                        : "border-border/70 bg-muted/20 hover:border-primary/40"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-medium">
                        {item.role} @ {item.company}
                      </p>
                      <StatusPill status={item.status} />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      checkpoint #{item.id} · {formatDateTime(item.created_at)}
                    </p>
                  </button>
                ))}
                {!approvals.data?.length ? (
                  <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
                    Nothing pending review.
                  </div>
                ) : null}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-border/70 bg-card/50">
          <CardHeader>
            <CardTitle className="text-sm">Review Detail</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {!selectedApproval ? (
              <p className="text-sm text-muted-foreground">Select an application to review.</p>
            ) : detail.isLoading ? (
              <p className="text-sm text-muted-foreground">Loading application detail...</p>
            ) : detail.data ? (
              <>
                <div className="grid gap-2 sm:grid-cols-2">
                  <div className="rounded-lg border border-border/70 p-3">
                    <p className="text-xs text-muted-foreground">Status</p>
                    <StatusPill status={detail.data.status} />
                  </div>
                  <div className="rounded-lg border border-border/70 p-3">
                    <p className="text-xs text-muted-foreground">Mode</p>
                    <p className="text-sm font-medium">{detail.data.mode}</p>
                  </div>
                </div>
                <div className="rounded-lg border border-border/70 p-3">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Generated Answers
                  </p>
                  <div className="space-y-2">
                    {detail.data.generated_answers.map((answer) => (
                      <div key={answer.id} className="rounded-lg bg-muted/30 p-2">
                        <p className="text-xs font-medium">{answer.question_text}</p>
                        <p className="text-xs text-muted-foreground">{answer.generated_text}</p>
                      </div>
                    ))}
                    {!detail.data.generated_answers.length ? (
                      <p className="text-xs text-muted-foreground">No generated answers recorded.</p>
                    ) : null}
                  </div>
                </div>

                <div className="rounded-lg border border-border/70 p-3">
                  <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Screenshots (recent global)
                  </p>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    {screenshots.data?.recent_screenshots.slice(0, 6).map((screenshot) => (
                      <p key={screenshot.path} className="truncate">
                        {screenshot.name}
                      </p>
                    ))}
                  </div>
                </div>

                <Textarea
                  placeholder="Review notes..."
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                  className="min-h-24"
                />

                <div className="flex flex-wrap gap-2">
                  {selectedApproval.ai_summary ? (
                    <p className="text-sm text-muted-foreground">{selectedApproval.ai_summary}</p>
                  ) : null}
                  <Button onClick={handleApprove} disabled={approveCheckpoint.isPending}>
                    <CheckCircle2 className="mr-2 size-4" />
                    Approve
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() => {
                      void api.openBrowserForCheckpoint(selectedApproval.id)
                      toast.info("Browser session ready")
                    }}
                  >
                    Open in browser
                  </Button>
                  <Button
                    variant="destructive"
                    onClick={handleReject}
                    disabled={rejectCheckpoint.isPending}
                  >
                    <XCircle className="mr-2 size-4" />
                    Reject
                  </Button>
                </div>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">Unable to load detail.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
