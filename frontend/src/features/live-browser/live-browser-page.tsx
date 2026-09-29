"use client";

import { useMemo } from "react";
import { Pause, Play, Hand, Bot, Square, Check, X } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { StatusPill } from "@/components/workflow/status-pill";
import {
  useAutomationControl,
  useRuntimeSnapshot,
} from "@/hooks/use-console-queries";
import { useEventWebSocket } from "@/hooks/use-event-websocket";
import { api } from "@/services/api/endpoints";

export function LiveBrowserPage() {
  const snapshot = useRuntimeSnapshot();
  const { connected, runtime: wsRuntime, events } = useEventWebSocket();
  const control = useAutomationControl();

  const runtime = wsRuntime ?? snapshot.data;
  const screenshotSrc = useMemo(() => {
    if (!runtime?.last_screenshot) return null;
    return api.screenshotUrl(runtime.last_screenshot);
  }, [runtime?.last_screenshot]);

  const browserEvents = events.filter((e) => e.type.startsWith("browser."));

  return (
    <div className="space-y-4">
      <PageHeader
        title="Live Browser"
        description="Supervise Firefox automation in real time — screenshots, actions, and human override."
        right={
          <Badge variant={connected ? "default" : "secondary"}>
            {connected ? "WS Connected" : "WS Disconnected"}
          </Badge>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => control.pause.mutate()}
          disabled={control.pause.isPending}
        >
          <Pause className="mr-1 h-4 w-4" /> Pause AI
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => control.resume.mutate()}
          disabled={control.resume.isPending}
        >
          <Play className="mr-1 h-4 w-4" /> Resume AI
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={() => control.stop.mutate()}
          disabled={control.stop.isPending}
        >
          <Square className="mr-1 h-4 w-4" /> Stop AI
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => control.manual.mutate()}
          disabled={control.manual.isPending}
        >
          <Hand className="mr-1 h-4 w-4" /> Manual control
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => control.returnAi.mutate()}
          disabled={control.returnAi.isPending}
        >
          <Bot className="mr-1 h-4 w-4" /> Return to AI
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Current session</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>
              <span className="text-muted-foreground">State:</span>{" "}
              {runtime?.state ?? "—"}
            </p>
            <p>
              <span className="text-muted-foreground">Task:</span>{" "}
              {runtime?.current_task ?? "—"}
            </p>
            <p>
              <span className="text-muted-foreground">Form step:</span>{" "}
              {runtime?.current_form_step ?? "—"}
            </p>
            <p className="truncate">
              <span className="text-muted-foreground">URL:</span>{" "}
              {runtime?.current_url ?? "—"}
            </p>
            <p>
              <span className="text-muted-foreground">Title:</span>{" "}
              {runtime?.current_title ?? "—"}
            </p>
            {runtime?.last_error ? (
              <p className="text-destructive">{runtime.last_error}</p>
            ) : null}
            {runtime?.ai_summary ? (
              <p className="text-muted-foreground">{runtime.ai_summary}</p>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Live screenshot</CardTitle>
          </CardHeader>
          <CardContent>
            {screenshotSrc ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={screenshotSrc}
                alt="Browser screenshot"
                className="max-h-[400px] w-full rounded-md border object-contain bg-muted"
              />
            ) : (
              <p className="text-sm text-muted-foreground">
                No screenshot yet. Start discovery or an application to see live captures.
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Recent actions</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-64">
              <ul className="space-y-2 text-xs">
                {(runtime?.recent_actions ?? []).map((a, i) => (
                  <li key={`${a.timestamp}-${i}`} className="border-b pb-1">
                    <strong>{a.action}</strong> {a.detail ?? ""}
                    <div className="text-muted-foreground">{a.timestamp}</div>
                  </li>
                ))}
                {browserEvents.slice(0, 20).map((e, i) => (
                  <li key={`ws-${i}`} className="border-b pb-1 text-muted-foreground">
                    {e.type}
                  </li>
                ))}
              </ul>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Queued actions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-sm">
              {(runtime?.queued_actions ?? []).map((q) => (
                <li key={q.id} className="flex items-center justify-between gap-2">
                  <span>
                    {q.action} {q.detail ?? ""}
                  </span>
                  <span className="flex gap-1">
                    <Button size="icon" variant="ghost" className="h-7 w-7">
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button size="icon" variant="ghost" className="h-7 w-7">
                      <X className="h-3 w-3" />
                    </Button>
                  </span>
                </li>
              ))}
              {(runtime?.queued_actions?.length ?? 0) === 0 ? (
                <p className="text-muted-foreground">No queued actions</p>
              ) : null}
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
