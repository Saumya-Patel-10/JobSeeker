"use client";

import { BrainCircuit, Search } from "lucide-react";

import { LogoMark } from "@/components/brand/logo";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { Button } from "@/components/ui/button";
import { useStatus } from "@/hooks/use-console-queries";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";

export function Topbar() {
  const { data: status } = useStatus();
  const setCommandOpen = useUiStore((state) => state.setCommandOpen);
  const llmOnline = Boolean(status?.llm_reachable);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border bg-background/85 px-4 backdrop-blur-md sm:px-6">
      <div className="flex items-center gap-3">
        <span className="md:hidden">
          <LogoMark />
        </span>
        <Button
          variant="outline"
          className="h-9 w-9 justify-center px-0 text-muted-foreground sm:w-64 sm:justify-start sm:px-3"
          onClick={() => setCommandOpen(true)}
          aria-label="Open command palette"
        >
          <Search className="size-4 sm:mr-2" />
          <span className="hidden text-sm sm:inline">Search pages and jobs</span>
          <kbd className="ml-auto hidden rounded border border-border bg-muted px-1.5 text-[11px] text-muted-foreground sm:inline">
            Ctrl K
          </kbd>
        </Button>
      </div>

      <div className="flex items-center gap-1.5">
        <span className="hidden items-center gap-2 rounded-full border border-border px-3 py-1 text-xs text-muted-foreground sm:inline-flex">
          <BrainCircuit className="size-3.5" />
          <span>{status?.llm_provider ?? "Model"}</span>
          <span
            className={cn("size-1.5 rounded-full", llmOnline ? "bg-success" : "bg-warning")}
            aria-hidden="true"
          />
          <span className={llmOnline ? "text-success" : "text-warning"}>
            {llmOnline ? "online" : "offline"}
          </span>
        </span>
        <ThemeToggle />
      </div>
    </header>
  );
}
