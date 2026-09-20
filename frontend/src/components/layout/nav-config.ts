import type { LucideIcon } from "lucide-react";
import {
  Activity,
  AreaChart,
  Bot,
  BriefcaseBusiness,
  ClipboardCheck,
  FileText,
  Gauge,
  MonitorCog,
  Settings2,
  SlidersHorizontal,
  UserRound,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  description: string;
}

export const navItems: NavItem[] = [
  {
    label: "Dashboard",
    href: "/",
    icon: Gauge,
    description: "Overview of ingestion, review queue, and AI throughput",
  },
  {
    label: "Control Center",
    href: "/control-center",
    icon: SlidersHorizontal,
    description: "Run the AI job hunt workflows from the UI",
  },
  {
    label: "Jobs Explorer",
    href: "/jobs",
    icon: BriefcaseBusiness,
    description: "Filter jobs and inspect scoring",
  },
  {
    label: "Resume Studio",
    href: "/resume-studio",
    icon: FileText,
    description: "Compare master vs generated resumes",
  },
  {
    label: "Review Queue",
    href: "/review-queue",
    icon: ClipboardCheck,
    description: "Approve or reject pending applications",
  },
  {
    label: "Live Browser",
    href: "/live-browser",
    icon: Activity,
    description: "Real-time browser telemetry and human override",
  },
  {
    label: "AI Activity Console",
    href: "/ai-console",
    icon: Bot,
    description: "Trace prompts, outputs, and validation outcomes",
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: AreaChart,
    description: "Funnel, source effectiveness, and score distribution",
  },
  {
    label: "Profile Manager",
    href: "/profile",
    icon: UserRound,
    description: "Manage candidate profile and standard answers",
  },
  {
    label: "Settings",
    href: "/settings",
    icon: Settings2,
    description: "Edit preferences, job sources, and blacklist",
  },
  {
    label: "Browser Settings",
    href: "/settings/browser",
    icon: MonitorCog,
    description: "Manage Firefox profiles and persistent sessions",
  },
];
