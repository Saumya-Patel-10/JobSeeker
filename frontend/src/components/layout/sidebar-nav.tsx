"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { navItems } from "@/components/layout/nav-config";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

export function SidebarNav() {
  const pathname = usePathname();
  const collapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);

  return (
    <aside
      className={cn(
        "border-r border-border/80 bg-sidebar/70 backdrop-blur-xl transition-all",
        collapsed ? "w-16" : "w-72"
      )}
    >
      <div className="flex h-14 items-center justify-between px-3">
        <div className={cn("text-sm font-semibold tracking-wide", collapsed && "sr-only")}>
          Ops Console
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleSidebar}
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
        </Button>
      </div>
      <Separator />
      <ScrollArea className="h-[calc(100vh-3.5rem)]">
        <nav className="space-y-1 px-2 py-3">
          {navItems.map((item) => {
            const active =
              item.href === "/"
                ? pathname === item.href
                : pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link key={item.href} href={item.href}>
                <span
                  className={cn(
                    "group flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 text-sm text-muted-foreground transition-all hover:border-border/70 hover:bg-accent/60 hover:text-accent-foreground",
                    active && "border-border bg-accent text-accent-foreground shadow-sm"
                  )}
                >
                  <item.icon className="size-4 shrink-0" />
                  {!collapsed ? (
                    <span className="min-w-0">
                      <span className="block truncate font-medium">{item.label}</span>
                      <span className="block truncate text-[11px] text-muted-foreground">
                        {item.description}
                      </span>
                    </span>
                  ) : null}
                </span>
              </Link>
            );
          })}
        </nav>
      </ScrollArea>
    </aside>
  );
}
