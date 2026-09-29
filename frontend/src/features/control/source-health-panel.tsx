"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusPill } from "@/components/workflow/status-pill";
import { useSourceHealth } from "@/hooks/use-console-queries";

export function SourceHealthPanel() {
  const sources = useSourceHealth();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Job sources</CardTitle>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2 text-sm">
          {(sources.data ?? []).map((s) => (
            <li
              key={s.name}
              className="flex flex-wrap items-center justify-between gap-2 rounded border p-2"
            >
              <div>
                <div className="font-medium">{s.name}</div>
                <div className="text-xs text-muted-foreground">{s.type}</div>
              </div>
              <StatusPill status={s.health_status} />
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
