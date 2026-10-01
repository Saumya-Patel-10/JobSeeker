"use client";

import { BrainCircuit, Search, Layers } from "lucide-react";
import Link from "next/link";

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
  const backendOnline = Boolean(status?.healthy);

  return (
    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border/80 bg-background/80 px-4 backdrop-blur-xl sm:px-6">
      <div className="flex items-center gap-3">
        <span className="md:hidden">
          <LogoMark />
        </span>
        <Button
          variant="outline"
          className="h-9 w-9 justify-center rounded-lg border-border/80 bg-card/60 px-0 text-muted-foreground shadow-sm transition-all hover:border-primary/40 hover:text-foreground sm:w-64 sm:justify-start sm:px-3"
          onClick={() => setCommandOpen(true)}
          aria-label="Open command palette"
        >
          <Search className="size-4 sm:mr-2 text-muted-foreground" />
          <span className="hidden text-xs sm:inline">Search jobs, tracks, commands...</span>
          <kbd className="ml-auto hidden rounded border border-border bg-muted/80 px-1.5 py-0.5 text-[10px] font-mono text-muted-foreground sm:inline">
            Ctrl K
          </kbd>
        </Button>
      </div>

      <div className="flex items-center gap-2">
        {/* Active Track indicator */}
        <Link
          href="/jobs"
          className="hidden items-center gap-1.5 rounded-full border border-indigo-500/25 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-600 transition-all hover:bg-indigo-500/15 dark:border-indigo-500/30 dark:bg-indigo-500/15 dark:text-indigo-300 md:inline-flex"
          title="Active Target Tracks"
        >
          <Layers className="size-3.5 text-indigo-500" />
          <span>Full-Stack · Frontend · Backend · AI</span>
        </Link>

        {/* Backend & AI status pill */}
        <span className="inline-flex items-center gap-2 rounded-full border border-border/80 bg-card/60 px-3 py-1 text-xs text-muted-foreground shadow-xs">
          <span className="relative flex size-2">
            <span
              className={cn(
                "absolute inline-flex h-full w-full rounded-full opacity-75",
                backendOnline && llmOnline ? "animate-ping bg-emerald-400" : "bg-amber-400"
              )}
            />
            <span
              className={cn(
                "relative inline-flex size-2 rounded-full",
                backendOnline && llmOnline ? "bg-emerald-500" : "bg-amber-500"
              )}
            />
          </span>
          <BrainCircuit className="size-3.5 text-muted-foreground" />
          <span className="hidden font-medium sm:inline">
            {status?.llm_provider ? `${status.llm_provider}` : "AI Engine"}
          </span>
          <span
            className={cn(
              "text-[11px] font-semibold",
              llmOnline ? "text-emerald-600 dark:text-emerald-400" : "text-amber-600 dark:text-amber-400"
            )}
          >
            {llmOnline ? "Ready" : "Offline"}
          </span>
        </span>

        <ThemeToggle />
      </div>
    </header>
  );
}
