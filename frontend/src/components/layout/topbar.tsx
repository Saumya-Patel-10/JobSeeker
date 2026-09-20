"use client";

import { useTheme } from "next-themes";
import { Bell, BrainCircuit, Database, Moon, Search, Sun, Terminal } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStatus } from "@/hooks/use-console-queries";
import { useUiStore } from "@/stores/ui-store";

export function Topbar() {
  const { data: status } = useStatus();
  const setCommandOpen = useUiStore((state) => state.setCommandOpen);
  const { theme, setTheme } = useTheme();
  const isDark = theme !== "light";

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/80 bg-background/65 px-4 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          className="h-9 w-72 justify-start text-muted-foreground"
          onClick={() => setCommandOpen(true)}
        >
          <Search className="mr-2 size-4" />
          <span className="text-sm">Command palette...</span>
          <kbd className="ml-auto rounded border border-border px-1.5 text-xs text-muted-foreground">
            Ctrl+K
          </kbd>
        </Button>
      </div>
      <div className="flex items-center gap-2">
        <Badge variant="outline" className="gap-1 text-xs">
          <BrainCircuit className="size-3.5" />
          {status?.llm_provider ?? "llm"}
          <span className={status?.llm_reachable ? "text-emerald-400" : "text-amber-400"}>
            {status?.llm_reachable ? "online" : "offline"}
          </span>
        </Badge>
        <Badge variant="outline" className="gap-1 text-xs">
          {status?.browser_engine ?? "firefox"}
          <span
            className={status?.browser_profile_has_cookies ? "text-emerald-400" : "text-amber-400"}
          >
            {status?.browser_profile_has_cookies ? "session" : "no-session"}
          </span>
        </Badge>
        <Badge variant="outline" className="gap-1 text-xs">
          <Database className="size-3.5" />
          <span className={status?.db_exists ? "text-emerald-400" : "text-amber-400"}>
            {status?.db_exists ? "db ok" : "db missing"}
          </span>
        </Badge>
        <Badge variant="outline" className="gap-1 text-xs">
          <Terminal className="size-3.5" />
          {status?.apply_default_mode ?? "human_review"}
        </Badge>
        <Button variant="ghost" size="icon" onClick={() => setTheme(isDark ? "light" : "dark")}>
          {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>
        <Button variant="ghost" size="icon">
          <Bell className="size-4" />
        </Button>
      </div>
    </header>
  );
}
