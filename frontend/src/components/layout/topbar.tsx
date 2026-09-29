"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTheme } from "next-themes";
import { Bell, BrainCircuit, Database, Moon, Search, Sun, Terminal, User, LogOut, Sparkles } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useStatus } from "@/hooks/use-console-queries";
import { useUiStore } from "@/stores/ui-store";
import { toast } from "sonner";

interface UserProfile {
  name: string;
  email: string;
  signedIn: boolean;
}

export function Topbar() {
  const router = useRouter();
  const { data: status } = useStatus();
  const setCommandOpen = useUiStore((state) => state.setCommandOpen);
  const { theme, setTheme } = useTheme();
  const isDark = theme !== "light";

  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("jobai_user");
      if (stored) {
        try {
          setUser(JSON.parse(stored));
        } catch {
          setUser(null);
        }
      }
    }
  }, []);

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("jobai_user");
      setUser(null);
    }
    toast.success("Signed out successfully.");
    router.push("/login");
  };

  return (
    <header className="flex h-14 items-center justify-between border-b border-border/80 bg-background/65 px-4 backdrop-blur-xl">
      <div className="flex items-center gap-3">
        <Button
          variant="outline"
          className="h-9 w-64 justify-start text-muted-foreground"
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
        <Badge variant="outline" className="hidden sm:inline-flex gap-1 text-xs">
          <BrainCircuit className="size-3.5" />
          {status?.llm_provider ?? "llm"}
          <span className={status?.llm_reachable ? "text-emerald-400" : "text-amber-400"}>
            {status?.llm_reachable ? "online" : "offline"}
          </span>
        </Badge>
        <Badge variant="outline" className="hidden md:inline-flex gap-1 text-xs">
          <Terminal className="size-3.5" />
          {status?.apply_default_mode ?? "human_review"}
        </Badge>

        <Button variant="ghost" size="icon" onClick={() => setTheme(isDark ? "light" : "dark")}>
          {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
        </Button>

        {user ? (
          <div className="flex items-center gap-2 pl-1 border-l border-border/60">
            <Link href="/onboarding">
              <Button variant="ghost" size="sm" className="h-8 gap-1.5 text-xs px-2">
                <div className="flex size-5 items-center justify-center rounded-full bg-primary/20 text-primary text-[10px] font-bold">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <span className="max-w-[100px] truncate hidden sm:inline">{user.name}</span>
              </Button>
            </Link>
            <Button
              variant="ghost"
              size="icon"
              className="size-8 text-muted-foreground hover:text-destructive"
              onClick={handleLogout}
              title="Sign Out"
            >
              <LogOut className="size-3.5" />
            </Button>
          </div>
        ) : (
          <Link href="/login">
            <Button size="sm" variant="default" className="text-xs h-8 gap-1.5">
              <User className="size-3.5" /> Sign In
            </Button>
          </Link>
        )}
      </div>
    </header>
  );
}
