"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, Sun, Moon } from "lucide-react";
import { useTheme } from "next-themes";
import { CommandPalette } from "@/components/layout/command-palette";
import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Topbar } from "@/components/layout/topbar";
import { Button } from "@/components/ui/button";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const isDark = theme !== "light";

  const isAuthOrPayment =
    pathname.startsWith("/login") ||
    pathname.startsWith("/signup") ||
    pathname.startsWith("/checkout") ||
    pathname.startsWith("/select-plan");

  if (isAuthOrPayment) {
    return (
      <div className="min-h-screen flex flex-col bg-background text-foreground">
        <header className="flex h-14 items-center justify-between border-b border-border/80 px-6 bg-background/80 backdrop-blur-md">
          <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
            <div className="flex size-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Bot className="size-4" />
            </div>
            <span className="text-sm">Job Finding AI</span>
          </Link>

          <div className="flex items-center gap-3">
            {pathname.startsWith("/login") ? (
              <Link href="/signup">
                <Button variant="outline" size="sm" className="text-xs">
                  Create Account
                </Button>
              </Link>
            ) : pathname.startsWith("/signup") ? (
              <Link href="/login">
                <Button variant="outline" size="sm" className="text-xs">
                  Sign In
                </Button>
              </Link>
            ) : (
              <Link href="/login">
                <Button variant="ghost" size="sm" className="text-xs">
                  Sign In
                </Button>
              </Link>
            )}
            <Button
              variant="ghost"
              size="icon"
              className="size-8"
              onClick={() => setTheme(isDark ? "light" : "dark")}
            >
              {isDark ? <Sun className="size-4" /> : <Moon className="size-4" />}
            </Button>
          </div>
        </header>

        <main className="flex-1 overflow-auto">{children}</main>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <SidebarNav />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="min-h-0 flex-1 overflow-auto p-4">{children}</main>
      </div>
      <CommandPalette />
    </div>
  );
}
