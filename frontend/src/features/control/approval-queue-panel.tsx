"use client";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useApproveCheckpoint,
  usePendingApprovals,
  useRejectCheckpoint,
} from "@/hooks/use-console-queries";
export function ApprovalQueuePanel() {
  const pending = usePendingApprovals();
  const approve = useApproveCheckpoint();
  const reject = useRejectCheckpoint();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Approval queue</CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-72">
          <ul className="space-y-3">
            {(pending.data ?? []).map((item) => (
              <li key={item.id} className="rounded-md border p-3 text-sm">
                <div className="font-medium">
                  {item.role} @ {item.company}
                </div>
                <div className="text-muted-foreground">
                  Confidence: {item.confidence?.toFixed(2) ?? "—"} · {item.checkpoint_type}
                </div>
                {item.ai_summary ? (
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {item.ai_summary}
                  </p>
                ) : null}
                {item.risks.length > 0 ? (
                  <ul className="mt-1 list-disc pl-4 text-xs text-amber-600">
                    {item.risks.map((r) => (
                      <li key={r}>{r}</li>
                    ))}
                  </ul>
                ) : null}
                <div className="mt-2 flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    onClick={async () => {
                      await approve.mutateAsync({ id: item.id, submit: false });
                      toast.success("Approved — review in Firefox before submit");
                    }}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="default"
                    onClick={async () => {
                      const res = await approve.mutateAsync({ id: item.id, submit: true });
                      toast.success(
                        res && typeof res === "object" && "submitted" in res && res.submitted
                          ? "Approved and submitted"
                          : "Approved (submit blocked or assist-only)"
                      );
                    }}
                  >
                    Approve & submit
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    onClick={async () => {
                      await fetch(
                        `${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000"}/approvals/${item.id}/open-browser`,
                        { method: "POST" }
                      );
                      toast.info("Browser session focused");
                    }}
                  >
                    Open in browser
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => reject.mutate(item.id)}
                  >
                    Reject
                  </Button>
                </div>
              </li>
            ))}
            {(pending.data?.length ?? 0) === 0 ? (
              <p className="text-muted-foreground">No pending approvals</p>
            ) : null}
          </ul>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
