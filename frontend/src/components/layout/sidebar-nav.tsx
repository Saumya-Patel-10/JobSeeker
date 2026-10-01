"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen } from "lucide-react";

import { Logo, LogoMark } from "@/components/brand/logo";
import { isActivePath, navGroups, settingsNavItem } from "@/components/layout/nav-config";
import type { NavItem } from "@/components/layout/nav-config";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useStatus } from "@/hooks/use-console-queries";
import { cn } from "@/lib/utils";
import { useUiStore } from "@/stores/ui-store";

function NavLink({ item, collapsed, active }: { item: NavItem; collapsed: boolean; active: boolean }) {
  return (
    <Link
      href={item.href}
      title={collapsed ? item.label : undefined}
      aria-current={active ? "page" : undefined}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-all duration-150",
        collapsed && "justify-center px-0 py-2.5",
        active
          ? "bg-primary/10 font-semibold text-primary shadow-xs dark:bg-primary/20"
          : "text-muted-foreground hover:bg-muted/70 hover:text-foreground"
      )}
    >
      {active && !collapsed && (
        <span
          className="absolute left-0 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-primary"
          aria-hidden="true"
        />
      )}
      <item.icon
        className={cn(
          "size-4 shrink-0 transition-transform duration-150 group-hover:scale-110",
          active ? "text-primary" : "text-muted-foreground group-hover:text-foreground"
        )}
      />
      {collapsed ? (
        <span className="sr-only">{item.label}</span>
      ) : (
        <span className="truncate">{item.label}</span>
      )}
    </Link>
  );
}

export function SidebarNav() {
  const pathname = usePathname();
  const collapsed = useUiStore((state) => state.sidebarCollapsed);
  const toggleSidebar = useUiStore((state) => state.toggleSidebar);
  const { data: status, isError } = useStatus();

  const backendUp = !isError && Boolean(status?.healthy);

  return (
    <aside
      className={cn(
        "hidden shrink-0 flex-col border-r border-border/80 bg-sidebar/95 backdrop-blur-xl transition-[width] duration-200 md:flex",
        collapsed ? "w-[68px]" : "w-64"
      )}
    >
      <div className={cn("flex h-14 items-center px-4", collapsed ? "justify-center" : "justify-between")}>
        {collapsed ? <LogoMark /> : <Logo href="/dashboard" />}
        {collapsed ? null : (
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            aria-label="Collapse sidebar"
            className="size-8 rounded-lg text-muted-foreground hover:bg-muted"
          >
            <PanelLeftClose className="size-4" />
          </Button>
        )}
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <nav aria-label="Main" className="space-y-6 px-3 py-4">
          {navGroups.map((group, index) => (
            <div key={group.label ?? `group-${index}`} className="space-y-1">
              {group.label && !collapsed ? (
                <p className="px-3 pb-1.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground/70">
                  {group.label}
                </p>
              ) : null}
              {group.label && collapsed ? <div className="mx-2 my-2 h-px bg-border/60" /> : null}
              {group.items.map((item) => (
                <NavLink
                  key={item.href}
                  item={item}
                  collapsed={collapsed}
                  active={isActivePath(pathname, item.href)}
                />
              ))}
            </div>
          ))}
        </nav>
      </ScrollArea>

      <div className="space-y-2 border-t border-border/80 p-3">
        <NavLink
          item={settingsNavItem}
          collapsed={collapsed}
          active={isActivePath(pathname, settingsNavItem.href)}
        />

        {collapsed ? (
          <Button
            variant="ghost"
            size="icon"
            className="mx-auto flex size-8 rounded-lg text-muted-foreground hover:bg-muted"
            onClick={toggleSidebar}
            aria-label="Expand sidebar"
          >
            <PanelLeftOpen className="size-4" />
          </Button>
        ) : (
          <div className="flex items-center justify-between rounded-xl border border-border/60 bg-muted/40 px-3 py-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span className="relative flex size-2">
                <span
                  className={cn(
                    "absolute inline-flex h-full w-full rounded-full opacity-75",
                    backendUp ? "animate-ping bg-emerald-400" : "bg-amber-400"
                  )}
                />
                <span
                  className={cn(
                    "relative inline-flex size-2 rounded-full",
                    backendUp ? "bg-emerald-500" : "bg-amber-500"
                  )}
                />
              </span>
              <span className="font-medium text-foreground/80">
                {backendUp ? "System Live" : "API Offline"}
              </span>
            </div>
            <span className="text-[10px] font-mono text-muted-foreground/80">
              {backendUp ? "v1.1" : "paused"}
            </span>
          </div>
        )}
      </div>
    </aside>
  );
}
