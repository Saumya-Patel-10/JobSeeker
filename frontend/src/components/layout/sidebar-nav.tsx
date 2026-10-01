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
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground",
        collapsed && "justify-center px-0",
        active && "bg-accent text-accent-foreground hover:bg-accent hover:text-accent-foreground"
      )}
    >
      <item.icon className="size-4 shrink-0" />
      {collapsed ? <span className="sr-only">{item.label}</span> : <span className="truncate">{item.label}</span>}
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
        "hidden shrink-0 flex-col border-r border-border bg-sidebar transition-[width] duration-200 md:flex",
        collapsed ? "w-[68px]" : "w-60"
      )}
    >
      <div className={cn("flex h-14 items-center px-3", collapsed ? "justify-center" : "justify-between")}>
        {collapsed ? <LogoMark /> : <Logo href="/dashboard" />}
        {collapsed ? null : (
          <Button variant="ghost" size="icon" onClick={toggleSidebar} aria-label="Collapse sidebar">
            <PanelLeftClose className="size-4" />
          </Button>
        )}
      </div>

      <ScrollArea className="min-h-0 flex-1">
        <nav aria-label="Main" className="space-y-5 px-3 py-3">
          {navGroups.map((group, index) => (
            <div key={group.label ?? `group-${index}`} className="space-y-1">
              {group.label && !collapsed ? (
                <p className="px-3 pb-1 text-[11px] font-medium uppercase tracking-wider text-muted-foreground/80">
                  {group.label}
                </p>
              ) : null}
              {group.label && collapsed ? <div className="mx-3 my-2 h-px bg-border" /> : null}
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

      <div className="space-y-2 border-t border-border p-3">
        <NavLink
          item={settingsNavItem}
          collapsed={collapsed}
          active={isActivePath(pathname, settingsNavItem.href)}
        />

        {collapsed ? (
          <Button variant="ghost" size="icon" className="mx-auto flex" onClick={toggleSidebar} aria-label="Expand sidebar">
            <PanelLeftOpen className="size-4" />
          </Button>
        ) : (
          <div className="flex items-center gap-2 rounded-lg bg-muted/60 px-3 py-2 text-xs text-muted-foreground">
            <span
              className={cn("size-2 rounded-full", backendUp ? "bg-success" : "bg-warning")}
              aria-hidden="true"
            />
            {backendUp ? "Backend connected" : "Backend offline"}
          </div>
        )}
      </div>
    </aside>
  );
}
