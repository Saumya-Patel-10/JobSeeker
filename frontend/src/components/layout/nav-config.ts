import type { LucideIcon } from "lucide-react";
import {
  AreaChart,
  Bot,
  BriefcaseBusiness,
  ClipboardCheck,
  FileText,
  LayoutDashboard,
  MonitorCog,
  MonitorPlay,
  Rocket,
  Settings2,
  UserRound,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
}

export interface NavGroup {
  label: string | null;
  items: NavItem[];
}

export const navGroups: NavGroup[] = [
  {
    label: null,
    items: [
      {
        label: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        description: "Today at a glance",
      },
      {
        label: "Jobs",
        href: "/jobs",
        icon: BriefcaseBusiness,
        description: "Discovered jobs and fit scores",
      },
      {
        label: "Applications",
        href: "/review-queue",
        icon: ClipboardCheck,
        description: "Review and approve applications",
      },
      {
        label: "Resume",
        href: "/resume-studio",
        icon: FileText,
        description: "Master and tailored resumes",
      },
      {
        label: "Profile",
        href: "/profile",
        icon: UserRound,
        description: "Your details and standard answers",
      },
    ],
  },
  {
    label: "Automation",
    items: [
      {
        label: "Job hunt",
        href: "/control-center",
        icon: Rocket,
        description: "Start, pause, and configure hunts",
      },
      {
        label: "Live browser",
        href: "/live-browser",
        icon: MonitorPlay,
        description: "Watch the automation session",
      },
      {
        label: "Analytics",
        href: "/analytics",
        icon: AreaChart,
        description: "Funnel and source performance",
      },
      {
        label: "AI activity",
        href: "/ai-console",
        icon: Bot,
        description: "Model calls and validation results",
      },
      {
        label: "Browser profiles",
        href: "/settings/browser",
        icon: MonitorCog,
        description: "Firefox profiles and saved logins",
      },
    ],
  },
];

export const settingsNavItem: NavItem = {
  label: "Settings",
  href: "/settings",
  icon: Settings2,
  description: "Preferences, sources, and blacklist",
};

/** Items shown in the mobile bottom bar. */
export const mobileNavItems: NavItem[] = [
  ...navGroups[0].items.filter((item) => item.href !== "/profile"),
  settingsNavItem,
];

/** Flat list used by the command palette. */
export const navItems: NavItem[] = [
  ...navGroups.flatMap((group) => group.items),
  settingsNavItem,
];

export function isActivePath(pathname: string, href: string): boolean {
  if (href === "/settings") {
    // Browser profiles live under /settings/browser but have their own nav entry.
    return pathname === "/settings";
  }
  return pathname === href || pathname.startsWith(`${href}/`);
}
