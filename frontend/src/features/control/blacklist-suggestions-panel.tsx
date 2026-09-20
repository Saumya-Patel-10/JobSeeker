"use client";

import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useApproveBlacklistSuggestion,
  useBlacklistSuggestions,
  useRejectBlacklistSuggestion,
} from "@/hooks/use-console-queries";
import { formatDateTime } from "@/utils/format";

export function BlacklistSuggestionsPanel() {
  const suggestions = useBlacklistSuggestions();
  const approve = useApproveBlacklistSuggestion();
  const reject = useRejectBlacklistSuggestion();

  const rows = suggestions.data ?? [];

  return (
    <Card className="panel">
      <CardHeader>
        <CardTitle className="text-base">Suggested blacklist candidates</CardTitle>
        <p className="text-xs text-muted-foreground">
          AI suggestions only — approving updates blacklist.yaml; the agent never writes it
          directly.
        </p>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[280px]">
          <div className="space-y-2 pr-2">
            {rows.map((row) => (
              <div
                key={row.id}
                className="rounded-xl border border-border/70 p-3 text-sm"
              >
                <p className="font-medium">
                  {row.company} — {row.job_title}
                </p>
                <p className="text-xs text-muted-foreground">{row.reason}</p>
                <p className="text-[11px] text-muted-foreground">
                  {formatDateTime(row.created_at)}
                </p>
                <div className="mt-2 flex gap-2">
                  <Button
                    size="sm"
                    disabled={approve.isPending}
                    onClick={async () => {
                      await approve.mutateAsync(row.id);
                      toast.success("Added to blacklist");
                    }}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={reject.isPending}
                    onClick={async () => {
                      await reject.mutateAsync(row.id);
                      toast.message("Suggestion dismissed");
                    }}
                  >
                    Dismiss
                  </Button>
                </div>
              </div>
            ))}
            {!rows.length ? (
              <p className="text-sm text-muted-foreground">No pending suggestions.</p>
            ) : null}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
