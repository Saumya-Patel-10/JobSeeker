"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Zap,
  CheckCircle2,
  Clock,
  Play,
  Pause,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  AlertCircle,
  FileText,
  Bot,
  Terminal,
  Layers,
  ArrowUpRight,
  HelpCircle,
  Briefcase,
  Building,
  MapPin,
  Calendar,
  Send,
  Eye,
  Sliders,
  Award
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { useEventWebSocket } from "@/hooks/use-event-websocket";
import { useJobs, useApplications, useAnalyticsSummary } from "@/hooks/use-console-queries";

// Types
export interface JobFeedItem {
  id: string;
  title: string;
  company: string;
  location: string;
  remoteType: "Remote" | "Hybrid" | "On-site";
  salary: string;
  atsSource: "Greenhouse" | "Lever" | "Workday" | "Generic";
  matchScore: number;
  matchedSkills: string[];
  missingSkills: string[];
  postedTime: string;
}

export type KanbanStage = "pending" | "tailoring" | "applying" | "submitted" | "interviewing";

export interface ApplicationCard {
  id: string;
  jobTitle: string;
  company: string;
  stage: KanbanStage;
  matchScore: number;
  atsSource: string;
  appliedDate?: string;
  currentStepMessage?: string;
  hasTailoredResume?: boolean;
  hasCoverLetter?: boolean;
  hasInterviewGuide?: boolean;
}

export function CommandCenterDashboard() {
  // Real backend queries
  const backendJobs = useJobs({ limit: 10 });
  const backendApps = useApplications({ limit: 20 });
  const analytics = useAnalyticsSummary();
  const { connected, lastEvent } = useEventWebSocket();

  // Plan & Quota state (reads from onboarding if available, defaults to Pro)
  const [activePlan, setActivePlan] = useState<"free" | "starter" | "pro">("pro");
  const [appsUsedToday, setAppsUsedToday] = useState<number>(14);
  const planLimits = { free: 15, starter: 25, pro: 50 };
  const currentLimit = planLimits[activePlan];

  // Live Playwright Bot Telemetry state (Pathway 3 - Step 3)
  const [isBotActive, setIsBotActive] = useState<boolean>(true);
  const [botStatusMessage, setBotStatusMessage] = useState<string>("Filling out education section...");
  const [botLogs, setBotLogs] = useState<string[]>([
    "[03:45:12] Bot initialized. Target: Stripe - Frontend Engineer (Greenhouse ATS)",
    "[03:45:15] Page loaded. Detecting form schema via Playwright...",
    "[03:45:18] Inputting Candidate Name: Saumya Patel",
    "[03:45:20] Inputting Email: saumya.patel@example.com",
    "[03:45:23] Uploading ATS-tailored resume: Saumya_Patel_Stripe_ATS.pdf",
    "[03:45:26] Answered work authorization: 'Authorized to work in US' -> 'Yes'",
    "[03:45:29] Active step: Filling out education section..."
  ]);
  const [showLogDrawer, setShowLogDrawer] = useState<boolean>(false);

  // High Match Job Feed (Pathway 3 - Step 2A)
  const [jobFeed, setJobFeed] = useState<JobFeedItem[]>([
    {
      id: "job-1",
      title: "Frontend Software Engineer Intern",
      company: "Stripe",
      location: "San Francisco, CA",
      remoteType: "Hybrid",
      salary: "$55 - $65 / hr",
      atsSource: "Greenhouse",
      matchScore: 96,
      matchedSkills: ["React", "TypeScript", "Next.js", "Tailwind CSS"],
      missingSkills: ["Ruby"],
      postedTime: "2 hours ago"
    },
    {
      id: "job-2",
      title: "Software Engineer - AI Applications",
      company: "Scale AI",
      location: "San Francisco, CA",
      remoteType: "Remote",
      salary: "$130k - $160k",
      atsSource: "Lever",
      matchScore: 94,
      matchedSkills: ["Python", "FastAPI", "OpenAI API", "Docker", "PostgreSQL"],
      missingSkills: ["Kubernetes"],
      postedTime: "4 hours ago"
    },
    {
      id: "job-3",
      title: "Full Stack Engineer (New Grad)",
      company: "Datadog",
      location: "New York, NY",
      remoteType: "Hybrid",
      salary: "$125k - $155k",
      atsSource: "Greenhouse",
      matchScore: 91,
      matchedSkills: ["TypeScript", "React", "Python", "Redis", "Distributed Systems"],
      missingSkills: ["Go"],
      postedTime: "6 hours ago"
    },
    {
      id: "job-4",
      title: "Software Engineer - Autonomous Agents",
      company: "Anthropic",
      location: "San Francisco, CA",
      remoteType: "On-site",
      salary: "$160k - $210k",
      atsSource: "Greenhouse",
      matchScore: 89,
      matchedSkills: ["Python", "Playwright", "LLM APIs", "AsyncIO"],
      missingSkills: ["vLLM"],
      postedTime: "1 day ago"
    },
    {
      id: "job-5",
      title: "Backend Engineer Intern",
      company: "Robinhood",
      location: "Menlo Park, CA",
      remoteType: "Hybrid",
      salary: "$58 / hr",
      atsSource: "Lever",
      matchScore: 87,
      matchedSkills: ["Python", "FastAPI", "PostgreSQL", "Celery"],
      missingSkills: ["Kafka"],
      postedTime: "1 day ago"
    }
  ]);

  // Application Tracker Kanban (Pathway 3 - Step 2B)
  const [kanbanCards, setKanbanCards] = useState<ApplicationCard[]>([
    {
      id: "app-1",
      jobTitle: "Software Engineer - AI Applications",
      company: "Scale AI",
      stage: "applying",
      matchScore: 94,
      atsSource: "Lever",
      currentStepMessage: "Filling out education section...",
      hasTailoredResume: true,
      hasCoverLetter: true,
      hasInterviewGuide: true
    },
    {
      id: "app-2",
      jobTitle: "Frontend Software Engineer Intern",
      company: "Stripe",
      stage: "tailoring",
      matchScore: 96,
      atsSource: "Greenhouse",
      currentStepMessage: "AI tailoring resume bullets for Big Tech ATS...",
      hasTailoredResume: true,
      hasCoverLetter: true,
      hasInterviewGuide: true
    },
    {
      id: "app-3",
      jobTitle: "Full Stack Engineer (New Grad)",
      company: "Datadog",
      stage: "pending",
      matchScore: 91,
      atsSource: "Greenhouse",
      currentStepMessage: "Queued for automated submission",
      hasTailoredResume: true,
      hasCoverLetter: false,
      hasInterviewGuide: false
    },
    {
      id: "app-4",
      jobTitle: "Software Engineer - Platform",
      company: "Vercel",
      stage: "submitted",
      matchScore: 95,
      atsSource: "Workday",
      appliedDate: "Today, 1:20 AM",
      hasTailoredResume: true,
      hasCoverLetter: true,
      hasInterviewGuide: true
    },
    {
      id: "app-5",
      jobTitle: "AI Systems Engineering Intern",
      company: "Perplexity",
      stage: "interviewing",
      matchScore: 98,
      atsSource: "Greenhouse",
      appliedDate: "Yesterday",
      hasTailoredResume: true,
      hasCoverLetter: true,
      hasInterviewGuide: true
    }
  ]);

  // Modal inspection state
  const [selectedAppForModal, setSelectedAppForModal] = useState<ApplicationCard | null>(null);
  const [modalTab, setModalTab] = useState<"resume" | "cover_letter" | "interview">("interview");

  // Read saved plan on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const storedPlan = localStorage.getItem("jobai_user_plan") as "free" | "starter" | "pro";
      if (storedPlan) setActivePlan(storedPlan);
    }
  }, []);

  // Listen to WebSocket events to update bot status if available
  useEffect(() => {
    if (lastEvent?.payload?.message) {
      const msg = String(lastEvent.payload.message);
      setBotStatusMessage(msg);
      setBotLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${msg}`, ...prev].slice(0, 100));
    }
  }, [lastEvent]);

  // Interactive Playwright Simulation Runner (for demo and testing)
  const runSimulatedBot = () => {
    setIsBotActive(true);
    const steps = [
      "Navigating to job application page...",
      "Analyzing ATS DOM tree with Playwright...",
      "Typing candidate personal details...",
      "Attaching Big Tech ATS-optimized PDF resume...",
      "Filling out education section...",
      "Generating style-matching cover letter...",
      "Verifying required fields & checking for captchas...",
      "Form auto-filled cleanly! Prepared for submission."
    ];

    steps.forEach((step, idx) => {
      setTimeout(() => {
        setBotStatusMessage(step);
        setBotLogs((prev) => [`[${new Date().toLocaleTimeString()}] ${step}`, ...prev].slice(0, 50));
        if (idx === steps.length - 1) {
          toast.success("Playwright bot finished auto-filling application!");
        }
      }, (idx + 1) * 1100);
    });
  };

  // Move card across Kanban stages
  const advanceCard = (appId: string) => {
    const stageOrder: KanbanStage[] = ["pending", "tailoring", "applying", "submitted", "interviewing"];
    setKanbanCards((prev) =>
      prev.map((c) => {
        if (c.id === appId) {
          const currentIndex = stageOrder.indexOf(c.stage);
          const nextStage = stageOrder[Math.min(currentIndex + 1, stageOrder.length - 1)];
          return { ...c, stage: nextStage };
        }
        return c;
      })
    );
    toast.success("Application progressed to next stage!");
  };

  // Trigger 1-Click Auto Apply
  const handleAutoApply = (job: JobFeedItem) => {
    if (appsUsedToday >= currentLimit) {
      toast.error(`Daily limit of ${currentLimit} applications reached! Upgrade your plan for more.`);
      return;
    }

    setAppsUsedToday((prev) => prev + 1);
    const newCard: ApplicationCard = {
      id: `app-${Date.now()}`,
      jobTitle: job.title,
      company: job.company,
      stage: "tailoring",
      matchScore: job.matchScore,
      atsSource: job.atsSource,
      currentStepMessage: "AI tailoring resume bullets & ATS keywords...",
      hasTailoredResume: true,
      hasCoverLetter: activePlan !== "free",
      hasInterviewGuide: activePlan === "pro"
    };

    setKanbanCards((prev) => [newCard, ...prev]);
    toast.success(`Started auto-application for ${job.title} at ${job.company}!`);

    // Transition to applying after 1.5 seconds
    setTimeout(() => {
      setKanbanCards((prev) =>
        prev.map((c) => (c.id === newCard.id ? { ...c, stage: "applying" } : c))
      );
      runSimulatedBot();
    }, 1500);
  };

  const columns: { stage: KanbanStage; title: string; color: string; badge: string }[] = [
    { stage: "pending", title: "Pending", color: "border-slate-500", badge: "bg-slate-500/10 text-slate-400" },
    { stage: "tailoring", title: "Tailoring", color: "border-blue-500", badge: "bg-blue-500/10 text-blue-500" },
    { stage: "applying", title: "Applying", color: "border-amber-500", badge: "bg-amber-500/10 text-amber-500" },
    { stage: "submitted", title: "Submitted", color: "border-emerald-500", badge: "bg-emerald-500/10 text-emerald-500" },
    { stage: "interviewing", title: "Interviewing", color: "border-purple-500", badge: "bg-purple-500/10 text-purple-500" }
  ];

  return (
    <div className="space-y-6">
      {/* TOP COMMAND HEADER: PLAN QUOTA & OVERVIEW */}
      <section className="flex flex-col gap-4 rounded-xl border border-border/70 bg-card p-5 shadow-sm lg:flex-row lg:items-center lg:justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold tracking-tight">AI Command Center</h1>
            <Badge
              variant="outline"
              className={`text-xs font-semibold uppercase tracking-wider ${
                activePlan === "pro"
                  ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-500"
                  : activePlan === "starter"
                  ? "border-blue-500/40 bg-blue-500/10 text-blue-500"
                  : "border-border text-muted-foreground"
              }`}
            >
              {activePlan === "pro" ? "Pro Plan ($7.99/mo)" : activePlan === "starter" ? "Growth Plan ($3.99/mo)" : "Free Plan"}
            </Badge>
          </div>
          <p className="text-xs text-muted-foreground">
            Autonomous multi-engine job finder, ATS optimizer, and deterministic Playwright bot.
          </p>
        </div>

        {/* Daily Quota Counter Bar */}
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
          <div className="w-full sm:w-64 space-y-1.5 rounded-lg border border-border/60 bg-muted/30 p-2.5">
            <div className="flex justify-between text-xs">
              <span className="font-medium text-foreground flex items-center gap-1.5">
                <Zap className="size-3.5 text-primary" /> Daily Quota
              </span>
              <span className="font-semibold text-primary">
                {appsUsedToday} / {currentLimit} applied
              </span>
            </div>
            <Progress value={(appsUsedToday / currentLimit) * 100} className="h-2" />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>{currentLimit - appsUsedToday} remaining today</span>
              <span>Resets at 00:00 UTC</span>
            </div>
          </div>

          <div className="flex gap-2">
            <Link href="/onboarding">
              <Button variant="outline" size="sm" className="text-xs gap-1.5">
                <Sliders className="size-3.5" /> Re-run Wizard
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* STEP 3: LIVE STATUS UPDATES (PLAYWRIGHT BOT TELEMETRY) */}
      <section className="relative overflow-hidden rounded-xl border border-primary/40 bg-primary/5 p-4 shadow-sm">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-3">
            <div className="relative flex size-3">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex size-3 rounded-full bg-emerald-500" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-primary flex items-center gap-1">
                  <Bot className="size-3.5" /> Playwright Bot Live Telemetry
                </span>
                <Badge variant="outline" className="text-[10px] bg-background/80 text-foreground py-0">
                  {connected ? "WebSocket Connected" : "Local Telemetry Active"}
                </Badge>
              </div>
              <p className="truncate text-sm font-medium text-foreground mt-0.5">
                &ldquo;{botStatusMessage}&rdquo;
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <Button
              variant="outline"
              size="sm"
              onClick={runSimulatedBot}
              className="text-xs gap-1.5 bg-background/80 hover:bg-background"
            >
              <Play className="size-3 text-emerald-500" /> Simulate Bot Step
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowLogDrawer(!showLogDrawer)}
              className="text-xs gap-1.5"
            >
              <Terminal className="size-3.5" /> {showLogDrawer ? "Hide Terminal" : "Bot Terminal"}
            </Button>
          </div>
        </div>

        {/* Expandable Live Bot Terminal */}
        <AnimatePresence>
          {showLogDrawer && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="mt-3 overflow-hidden rounded-lg bg-black/90 p-3 font-mono text-[11px] text-emerald-400 border border-emerald-500/20"
            >
              <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-white/10 text-slate-400 text-[10px]">
                <span>Playwright Headless Browser stdout & event log</span>
                <span className="flex items-center gap-1">
                  <span className="size-1.5 rounded-full bg-emerald-500 animate-pulse" /> STREAMING
                </span>
              </div>
              <div className="max-h-40 overflow-y-auto space-y-1">
                {botLogs.map((log, index) => (
                  <div key={index} className="leading-tight">
                    {log}
                  </div>
                ))}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </section>

      {/* STEP 2: HIGH MATCH JOB FEED & KANBAN TRACKER */}
      <Tabs defaultValue="tracker" className="space-y-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <TabsList className="grid w-full grid-cols-2 sm:w-auto">
            <TabsTrigger value="tracker" className="text-xs gap-1.5">
              <Layers className="size-3.5" /> Application Tracker (Kanban)
            </TabsTrigger>
            <TabsTrigger value="feed" className="text-xs gap-1.5">
              <Sparkles className="size-3.5 text-primary" /> High-Match Job Feed ({jobFeed.length})
            </TabsTrigger>
          </TabsList>

          <span className="text-xs text-muted-foreground hidden sm:inline">
            Drag or click cards to progress applications
          </span>
        </div>

        {/* 2B: APPLICATION TRACKER (KANBAN STYLE BOARD) */}
        <TabsContent value="tracker" className="space-y-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
            {columns.map((col) => {
              const colCards = kanbanCards.filter((card) => card.stage === col.stage);
              return (
                <div
                  key={col.stage}
                  className="flex flex-col rounded-xl border border-border/80 bg-muted/20 p-3 min-h-[460px]"
                >
                  {/* Column Header */}
                  <div className="flex items-center justify-between pb-2 mb-3 border-b border-border/60">
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-semibold">{col.title}</span>
                      <Badge variant="secondary" className={`text-[10px] px-1.5 py-0 ${col.badge}`}>
                        {colCards.length}
                      </Badge>
                    </div>
                  </div>

                  {/* Cards inside Column */}
                  <div className="space-y-2.5 flex-1">
                    {colCards.map((card) => (
                      <motion.div
                        key={card.id}
                        layout
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="group relative rounded-lg border border-border/80 bg-card p-3 shadow-xs hover:border-primary/70 hover:shadow-sm transition-all cursor-pointer"
                        onClick={() => setSelectedAppForModal(card)}
                      >
                        <div className="flex items-start justify-between gap-1">
                          <span className="text-[10px] font-semibold text-muted-foreground uppercase">
                            {card.company}
                          </span>
                          <Badge
                            variant="outline"
                            className="text-[10px] px-1.5 py-0 bg-emerald-500/10 text-emerald-500 border-emerald-500/30"
                          >
                            {card.matchScore}% Match
                          </Badge>
                        </div>

                        <h4 className="text-xs font-semibold text-foreground line-clamp-2 mt-1">
                          {card.jobTitle}
                        </h4>

                        <div className="mt-2 flex items-center gap-2 text-[11px] text-muted-foreground">
                          <Badge variant="secondary" className="text-[9px] px-1 py-0">
                            {card.atsSource}
                          </Badge>
                          {card.appliedDate && <span>{card.appliedDate}</span>}
                        </div>

                        {/* Live Bot message indicator on applying card */}
                        {card.stage === "applying" && (
                          <div className="mt-2.5 rounded bg-amber-500/10 p-1.5 text-[10px] text-amber-500 flex items-center gap-1.5 border border-amber-500/20 animate-pulse">
                            <Bot className="size-3 shrink-0" />
                            <span className="truncate">{card.currentStepMessage}</span>
                          </div>
                        )}

                        {/* Quick Action footer */}
                        <div className="mt-3 flex items-center justify-between border-t border-border/40 pt-2 text-[10px]">
                          <span className="text-muted-foreground flex items-center gap-1">
                            {card.hasInterviewGuide && activePlan === "pro" ? (
                              <Award className="size-3 text-purple-500" />
                            ) : (
                              <FileText className="size-3" />
                            )}
                            Details
                          </span>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              advanceCard(card.id);
                            }}
                            className="text-primary hover:underline font-medium flex items-center gap-0.5"
                          >
                            Advance <ChevronRight className="size-3" />
                          </button>
                        </div>
                      </motion.div>
                    ))}

                    {colCards.length === 0 && (
                      <div className="flex h-36 items-center justify-center rounded-lg border border-dashed border-border/60 text-center p-3">
                        <span className="text-[11px] text-muted-foreground">No applications</span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </TabsContent>

        {/* 2A: HIGH MATCH JOB FEED */}
        <TabsContent value="feed" className="space-y-4">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
            {jobFeed.map((job) => (
              <Card
                key={job.id}
                className="relative overflow-hidden border-border/80 transition-all hover:border-primary/70 hover:shadow-md"
              >
                <CardHeader className="pb-2">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-bold text-muted-foreground uppercase">{job.company}</span>
                        <Badge variant="outline" className="text-[10px] py-0">
                          {job.atsSource}
                        </Badge>
                      </div>
                      <CardTitle className="text-sm font-bold mt-1 line-clamp-1">{job.title}</CardTitle>
                    </div>

                    {/* Match Score Badge */}
                    <div className="flex flex-col items-end">
                      <span className="rounded-md bg-emerald-500/10 px-2 py-1 text-xs font-bold text-emerald-500 border border-emerald-500/30">
                        {job.matchScore}% Match
                      </span>
                      <span className="text-[10px] text-muted-foreground mt-0.5">{job.postedTime}</span>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="space-y-3 pb-3 text-xs">
                  <div className="flex items-center gap-3 text-muted-foreground text-[11px]">
                    <span className="flex items-center gap-1">
                      <MapPin className="size-3" /> {job.location}
                    </span>
                    <span>·</span>
                    <Badge variant="secondary" className="text-[10px] py-0">
                      {job.remoteType}
                    </Badge>
                    <span>·</span>
                    <span className="font-semibold text-foreground">{job.salary}</span>
                  </div>

                  {/* Matched & Missing Skills tags */}
                  <div className="space-y-1">
                    <span className="text-[10px] text-muted-foreground">Matched Skills:</span>
                    <div className="flex flex-wrap gap-1">
                      {job.matchedSkills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded bg-emerald-500/10 px-1.5 py-0.5 text-[10px] font-medium text-emerald-500 border border-emerald-500/20"
                        >
                          ✓ {skill}
                        </span>
                      ))}
                      {job.missingSkills.map((skill) => (
                        <span
                          key={skill}
                          className="rounded bg-muted px-1.5 py-0.5 text-[10px] text-muted-foreground"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </CardContent>

                <div className="flex items-center justify-between border-t border-border/60 p-3 pt-2.5 bg-muted/10">
                  <span className="text-[11px] text-muted-foreground">
                    {activePlan === "pro" ? "✓ Big Tech ATS Bypass Ready" : "✓ Standard Ingestion"}
                  </span>
                  <Button
                    size="sm"
                    onClick={() => handleAutoApply(job)}
                    className="text-xs gap-1.5 bg-primary text-primary-foreground hover:bg-primary/90"
                  >
                    <Zap className="size-3.5 fill-current" /> 1-Click Auto Apply
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>

      {/* INSPECT APPLICATION MODAL (TAILORED RESUME, COVER LETTER, INTERVIEW GUIDE) */}
      <Dialog open={selectedAppForModal !== null} onOpenChange={() => setSelectedAppForModal(null)}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
          {selectedAppForModal && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className="text-xs">
                    {selectedAppForModal.atsSource} ATS
                  </Badge>
                  <span className="text-xs font-semibold text-emerald-500">
                    {selectedAppForModal.matchScore}% Match Score
                  </span>
                </div>
                <DialogTitle className="text-base">
                  {selectedAppForModal.jobTitle} — {selectedAppForModal.company}
                </DialogTitle>
                <DialogDescription className="text-xs">
                  Inspect the AI-generated assets prepared for this application.
                </DialogDescription>
              </DialogHeader>

              <Tabs defaultValue={modalTab} onValueChange={(v) => setModalTab(v as any)} className="w-full mt-2">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="resume" className="text-xs">
                    <FileText className="size-3.5 mr-1" /> Tailored Resume
                  </TabsTrigger>
                  <TabsTrigger value="cover_letter" className="text-xs">
                    <Sparkles className="size-3.5 mr-1" /> Cover Letter
                  </TabsTrigger>
                  <TabsTrigger value="interview" className="text-xs">
                    <Award className="size-3.5 mr-1 text-purple-500" /> Interview Prep ($7.99)
                  </TabsTrigger>
                </TabsList>

                {/* Tab: Tailored Resume */}
                <TabsContent value="resume" className="space-y-3 pt-2 text-xs">
                  <div className="rounded-lg border border-border p-3 bg-muted/20 font-mono text-[11px] space-y-2">
                    <p className="font-bold text-foreground">SAUMYA PATEL — FULL STACK ENGINEER</p>
                    <p className="text-muted-foreground">San Francisco, CA · saumya.patel@example.com · github.com/saumya-patel</p>
                    <div className="border-t border-border/60 pt-2">
                      <p className="font-semibold text-primary">RELEVANT TECHNICAL HIGHLIGHTS (ATS TAILORED)</p>
                      <ul className="list-disc pl-4 space-y-1 text-foreground mt-1">
                        <li>
                          Architected deterministic browser automation pipeline using <strong>Playwright</strong> and <strong>TypeScript</strong>, cutting manual entry overhead by 92%.
                        </li>
                        <li>
                          Engineered high-throughput asynchronous backend in <strong>FastAPI</strong> and <strong>Redis</strong>, orchestrating distributed background queues.
                        </li>
                        <li>
                          Integrated structured LLM completion models with strict Zod validation schemas.
                        </li>
                      </ul>
                    </div>
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button size="sm" variant="outline" className="text-xs">
                      Download PDF
                    </Button>
                    <Button size="sm" variant="outline" className="text-xs">
                      Download DOCX
                    </Button>
                  </div>
                </TabsContent>

                {/* Tab: Cover Letter */}
                <TabsContent value="cover_letter" className="space-y-3 pt-2 text-xs">
                  <div className="rounded-lg border border-border p-4 bg-muted/20 text-xs leading-relaxed space-y-3">
                    <p className="text-muted-foreground">Dear Hiring Team at {selectedAppForModal.company},</p>
                    <p>
                      I am writing to express my strong enthusiasm for the {selectedAppForModal.jobTitle} position. With experience engineering scalable web applications and deterministic automation pipelines, I have closely followed your team&apos;s product velocity and developer-first architecture.
                    </p>
                    <p>
                      In my recent projects, I specialized in high-performance TypeScript and Python distributed systems, building agentic browser workflows and resilient API architectures. My focus on reliable, type-safe execution matches your emphasis on engineering rigor.
                    </p>
                    <p>
                      Thank you for your time and consideration. I welcome the opportunity to discuss how my skill set can support your upcoming product milestones.
                    </p>
                    <p className="text-muted-foreground">Sincerely,<br />Saumya Patel</p>
                  </div>
                  <Badge variant="outline" className="text-[10px] text-blue-500 border-blue-500/30">
                    Voice calibrated using your writing sample
                  </Badge>
                </TabsContent>

                {/* Tab: Role & Company Interview Prep Guide */}
                <TabsContent value="interview" className="space-y-3 pt-2 text-xs">
                  {activePlan === "pro" ? (
                    <div className="space-y-3">
                      <div className="rounded-lg border border-purple-500/30 bg-purple-500/10 p-3">
                        <h4 className="font-semibold text-purple-400 flex items-center gap-1.5 text-xs">
                          <Award className="size-4" /> Role & Company Interview Guide (Pro Tier Unlocked)
                        </h4>
                        <p className="text-muted-foreground text-[11px] mt-0.5">
                          Anticipated technical and behavioral questions customized for {selectedAppForModal.company}.
                        </p>
                      </div>

                      <div className="rounded-lg border border-border p-3 space-y-2">
                        <p className="font-semibold text-foreground">
                          Q1 (Technical): How would you handle flaky selectors or anti-bot bot challenges in automated pipelines?
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          <strong>Recommended STAR Answer:</strong> Explain your experience with Playwright persistent contexts, explicit wait states, stealth plugins, and how you separate deterministic DOM actions from LLM reasoning.
                        </p>
                      </div>

                      <div className="rounded-lg border border-border p-3 space-y-2">
                        <p className="font-semibold text-foreground">
                          Q2 (Behavioral): Describe a situation where you had to debug an intermittent race condition under tight deadlines.
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          <strong>Recommended STAR Answer:</strong> Highlight your Redis lock implementation, structured logging with correlation IDs, and idempotent retry strategies.
                        </p>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-dashed border-border p-6 text-center space-y-2">
                      <Award className="size-8 mx-auto text-purple-500 opacity-60" />
                      <h4 className="text-sm font-semibold">Unlock Company-Specific Interview Guides</h4>
                      <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                        Upgrade to the Pro Plan ($7.99/mo) to receive role-tailored technical & behavioral interview questions with custom STAR answers for every application.
                      </p>
                      <Button size="sm" className="mt-2 bg-purple-600 hover:bg-purple-700 text-white text-xs">
                        Upgrade to Pro ($7.99)
                      </Button>
                    </div>
                  )}
                </TabsContent>
              </Tabs>

              <DialogFooter className="border-t border-border/60 pt-3">
                <Button size="sm" variant="outline" onClick={() => setSelectedAppForModal(null)} className="text-xs">
                  Close
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    advanceCard(selectedAppForModal.id);
                    setSelectedAppForModal(null);
                  }}
                  className="text-xs gap-1"
                >
                  Advance Stage <ChevronRight className="size-3" />
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
