"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { apiBaseUrl } from "@/lib/env";
import { queryKeys } from "@/services/api/query-keys";
import type { RuntimeSnapshot } from "@/types/api";

export interface WsEvent {
  type: string;
  payload: Record<string, unknown>;
}

function wsUrl(): string {
  const base = apiBaseUrl.replace(/^http/, "ws");
  return `${base}/ws/events`;
}

export function useEventWebSocket() {
  const queryClient = useQueryClient();
  const [connected, setConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<WsEvent | null>(null);
  const [runtime, setRuntime] = useState<RuntimeSnapshot | null>(null);
  const [events, setEvents] = useState<WsEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;
    let retryMs = 1000;

    const connect = () => {
      if (cancelled) return;
      const ws = new WebSocket(wsUrl());
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryMs = 1000;
      };

      ws.onclose = () => {
        setConnected(false);
        if (!cancelled) {
          setTimeout(connect, retryMs);
          retryMs = Math.min(retryMs * 2, 30_000);
        }
      };

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as WsEvent;
          if (data.type === "ping") return;
          setLastEvent(data);
          setEvents((prev) => [data, ...prev].slice(0, 200));

          if (data.type === "runtime.snapshot") {
            const payload = data.payload as {
              automation?: RuntimeSnapshot;
            };
            if (payload.automation) setRuntime(payload.automation);
          }
          if (data.type === "automation.state") {
            setRuntime(data.payload as unknown as RuntimeSnapshot);
          }
          if (
            data.type.startsWith("approval.") ||
            data.type.startsWith("discovery.") ||
            data.type.startsWith("job_hunt.") ||
            data.type.startsWith("orchestrator.")
          ) {
            void queryClient.invalidateQueries({ queryKey: queryKeys.runtime });
            void queryClient.invalidateQueries({ queryKey: queryKeys.approvals });
            void queryClient.invalidateQueries({ queryKey: queryKeys.jobHuntStatus });
            void queryClient.invalidateQueries({ queryKey: queryKeys.blacklistSuggestions });
            void queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
          }
          if (data.type.startsWith("browser.")) {
            void queryClient.invalidateQueries({ queryKey: queryKeys.runtime });
          }
        } catch {
          /* ignore malformed */
        }
      };
    };

    connect();
    const ping = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, 25_000);

    return () => {
      cancelled = true;
      clearInterval(ping);
      wsRef.current?.close();
    };
  }, [queryClient]);

  return { connected, lastEvent, runtime, events };
}
