import Link from "next/link";
import {
  ArrowRight,
  Check,
  ChevronDown,
  FileText,
  Gauge,
  Lock,
  MonitorPlay,
  MousePointerClick,
  PenLine,
  Radar,
  Search,
  Send,
  ShieldCheck,
  Upload,
} from "lucide-react";

import { ProductPreview } from "@/components/marketing/product-preview";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const steps = [
  {
    icon: Upload,
    title: "Add your resume",
    body: "Keep one master resume and your preferences: roles, locations, salary, work authorization. That is the single source of truth.",
  },
  {
    icon: Search,
    title: "It finds and scores jobs",
    body: "New openings are pulled from your sources, filtered by your rules, and scored against your resume with a clear rationale.",
  },
  {
    icon: Send,
    title: "It tailors and applies",
    body: "For each good fit it rewrites your resume, drafts a cover letter, fills the application form, and sends it on your terms.",
  },
];

const features = [
  {
    icon: Radar,
    title: "Continuous discovery",
    body: "Greenhouse and Lever boards, browser-based sources, and any job URL you paste in.",
  },
  {
    icon: Gauge,
    title: "Explainable fit scores",
    body: "Skill overlap, seniority, location, and salary fit, with matched and missing skills for every job.",
  },
  {
    icon: FileText,
    title: "Resume tailored per job",
    body: "Rephrases and reorders what you already have to match the posting. Exports DOCX and PDF.",
  },
  {
    icon: PenLine,
    title: "Cover letters in your voice",
    body: "Generated from the job description and your own writing, not a generic template.",
  },
  {
    icon: MousePointerClick,
    title: "Automatic form filling",
    body: "A real browser fills standard fields and answers common questions from your profile.",
  },
  {
    icon: MonitorPlay,
    title: "Watch it work",
    body: "Live browser view with screenshots and an action log. Take over manually at any time.",
  },
];

const modes = [
  {
    name: "Manual review",
    body: "Everything is prepared, then it stops. You approve each application.",
    tag: "Default",
  },
  {
    name: "Assisted",
    body: "Scores jobs and tailors documents only. You do the applying.",
    tag: null,
  },
  {
    name: "Autonomous",
    body: "Fills and submits approved-by-rule applications within your daily limit.",
    tag: "Opt-in",
  },
];

const guardrails = [
  "Daily application limit and cooldown between applications",
  "Minimum match score before anything is prepared",
  "Company and keyword blacklist",
  "Pause everything with one click",
];

const faqs = [
  {
    q: "Does it submit applications without asking me?",
    a: "Only if you turn on autonomous mode and allow auto-submit in settings. By default each application stops at an approval checkpoint so you can review the resume and answers first.",
  },
  {
    q: "Which job sources are supported?",
    a: "Greenhouse and Lever through their public APIs, browser-based sources such as Raytheon, and any job URL you paste. LinkedIn is assist-only and never auto-submits.",
  },
  {
    q: "Where does my data live?",
    a: "On your machine. Applications, resumes, and history are stored locally, and the language model runs through LM Studio or Ollama.",
  },
  {
    q: "Will it invent experience I do not have?",
    a: "Tailoring rephrases and reorders your master resume to match a posting. Review the generated resume in the approval queue before anything is sent.",
  },
];

export default function LandingPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-border/70">
        <div className="bg-dots pointer-events-none absolute inset-0 opacity-50 [mask-image:linear-gradient(to_bottom,black,transparent_85%)]" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 sm:py-24 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="space-y-7">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
              <span className="size-1.5 rounded-full bg-primary" />
              Personal AI job-search assistant
            </span>

            <h1 className="text-4xl font-semibold tracking-tight text-balance sm:text-5xl lg:text-[3.4rem] lg:leading-[1.05]">
              Your resume, tailored and sent to every job that{" "}
              <span className="text-primary">fits</span>.
            </h1>

            <p className="max-w-xl text-lg leading-relaxed text-muted-foreground text-pretty">
              Upload once. The assistant finds new openings, rewrites your resume for each one, and
              prepares the application while you stay in control.
            </p>

            <div className="flex flex-wrap items-center gap-3">
              <Link
                href="/dashboard"
                className={cn(buttonVariants({ variant: "default" }), "h-11 gap-2 px-5 text-sm")}
              >
                Open dashboard
                <ArrowRight className="size-4" />
              </Link>
              <a
                href="#how-it-works"
                className={cn(buttonVariants({ variant: "outline" }), "h-11 px-5 text-sm")}
              >
                See how it works
              </a>
            </div>

            <p className="flex items-center gap-2 text-sm text-muted-foreground">
              <Lock className="size-4 text-primary" />
              Runs locally. You approve what gets sent.
            </p>
          </div>

          <ProductPreview className="lg:ml-auto lg:max-w-md" />
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="scroll-mt-16 border-b border-border/70">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="max-w-2xl">
            <p className="text-sm font-medium text-primary">How it works</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-balance">
              Three steps, then it runs in the background
            </h2>
          </div>

          <ol className="mt-12 grid gap-10 md:grid-cols-3">
            {steps.map((step, index) => (
              <li key={step.title} className="relative">
                <div className="flex items-center gap-3">
                  <span className="flex size-10 items-center justify-center rounded-full bg-accent text-accent-foreground">
                    <step.icon className="size-5" />
                  </span>
                  <span className="text-sm font-medium text-muted-foreground tabular">
                    Step {index + 1}
                  </span>
                </div>
                <h3 className="mt-4 text-lg font-semibold tracking-tight">{step.title}</h3>
                <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="scroll-mt-16 border-b border-border/70 bg-secondary/40">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="max-w-2xl">
            <p className="text-sm font-medium text-primary">Features</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight text-balance">
              Everything between &ldquo;new posting&rdquo; and &ldquo;application sent&rdquo;
            </h2>
          </div>

          <div className="mt-12 grid gap-x-10 gap-y-10 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.title} className="flex gap-4">
                <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-lg border border-border bg-card text-primary">
                  <feature.icon className="size-[18px]" />
                </span>
                <div>
                  <h3 className="font-semibold tracking-tight">{feature.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">
                    {feature.body}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Control */}
      <section id="control" className="scroll-mt-16 border-b border-border/70">
        <div className="mx-auto grid max-w-6xl gap-12 px-5 py-20 lg:grid-cols-2">
          <div className="space-y-6">
            <div>
              <p className="text-sm font-medium text-primary">Control</p>
              <h2 className="mt-2 text-3xl font-semibold tracking-tight text-balance">
                Automation that stays on a leash
              </h2>
              <p className="mt-4 text-[15px] leading-relaxed text-muted-foreground">
                Choose how hands-on you want to be. Every mode respects the same safety rules, and
                every application keeps a full history of what was sent.
              </p>
            </div>

            <ul className="space-y-3">
              {guardrails.map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm">
                  <span className="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground">
                    <Check className="size-3" />
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="space-y-3">
            {modes.map((mode) => (
              <div key={mode.name} className="rounded-xl border border-border bg-card p-5">
                <div className="flex items-center justify-between gap-3">
                  <h3 className="flex items-center gap-2 font-semibold tracking-tight">
                    <ShieldCheck className="size-4 text-primary" />
                    {mode.name}
                  </h3>
                  {mode.tag ? (
                    <span className="rounded-full bg-secondary px-2.5 py-0.5 text-xs font-medium text-muted-foreground">
                      {mode.tag}
                    </span>
                  ) : null}
                </div>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{mode.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="scroll-mt-16 border-b border-border/70 bg-secondary/40">
        <div className="mx-auto max-w-3xl px-5 py-20">
          <p className="text-sm font-medium text-primary">FAQ</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight">Common questions</h2>

          <div className="mt-10 divide-y divide-border rounded-xl border border-border bg-card">
            {faqs.map((item) => (
              <details key={item.q} className="group px-5 py-4">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium [&::-webkit-details-marker]:hidden">
                  {item.q}
                  <ChevronDown className="size-4 shrink-0 text-muted-foreground transition-transform group-open:rotate-180" />
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{item.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* Closing CTA */}
      <section>
        <div className="mx-auto max-w-6xl px-5 py-20 text-center">
          <h2 className="text-3xl font-semibold tracking-tight text-balance">
            Ready for your next application run?
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
            Open the dashboard, check your sources, and start a hunt.
          </p>
          <Link
            href="/dashboard"
            className={cn(buttonVariants({ variant: "default" }), "mt-7 h-11 gap-2 px-6 text-sm")}
          >
            Open dashboard
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>
    </>
  );
}
