"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Check,
  Zap,
  Sparkles,
  ShieldCheck,
  Star,
  FileCheck,
  X,
  ArrowRight,
  CreditCard,
  Lock,
  ArrowLeft
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";

export function SelectPlanPage() {
  const router = useRouter();
  const [selectedPlan, setSelectedPlan] = useState<"free" | "starter" | "pro">("pro");

  const handleSelectPlan = (plan: "free" | "starter" | "pro") => {
    setSelectedPlan(plan);

    if (plan === "free") {
      // Free plan: Save to storage and bypass payment portal directly to resume upload & profile questionnaire
      if (typeof window !== "undefined") {
        localStorage.setItem("jobai_user_plan", "free");
      }
      toast.success("Free Plan activated (15 apps/day)! Let's upload your resume.");
      router.push("/onboarding?step=resume");
    } else {
      // Paid plan ($3.99 or $7.99): Navigate to Payment Portal
      toast.info(`Redirecting to secure payment portal for ${plan === "starter" ? "$3.99 Growth" : "$7.99 Pro"} plan...`);
      router.push(`/checkout?plan=${plan}`);
    }
  };

  return (
    <div className="mx-auto max-w-5xl py-10 px-4">
      <div className="mb-8 text-center space-y-2">
        <Badge variant="outline" className="px-3 py-1 text-xs font-semibold text-primary border-primary/30 bg-primary/5">
          Step 2: Choose Your Plan
        </Badge>
        <h1 className="text-3xl font-extrabold tracking-tight">Select your AI Automation Level</h1>
        <p className="text-sm text-muted-foreground max-w-xl mx-auto">
          Choose between our Free plan for basic job matching, or upgrade to unlock custom ATS bypass, style-mimicking cover letters, and high-volume daily applications.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* FREE PLAN CARD */}
        <Card
          className={`relative flex flex-col justify-between transition-all duration-200 hover:border-primary/80 ${
            selectedPlan === "free" ? "border-primary ring-2 ring-primary/20 shadow-lg" : "border-border/80"
          }`}
        >
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-xs">Zero Cost</Badge>
            </div>
            <CardTitle className="text-xl font-bold mt-2">Free Plan</CardTitle>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-3xl font-extrabold">$0</span>
              <span className="text-xs text-muted-foreground">/ month</span>
            </div>
            <CardDescription className="text-xs">
              Casual job hunting with automated discovery and basic auto-fill.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3.5 text-xs">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <Zap className="size-4 text-primary shrink-0" />
              <span><strong>10–15 applications</strong> / day</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Check className="size-3.5 text-emerald-500 shrink-0" />
              <span>Automated job opening radar (Greenhouse & Lever)</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Check className="size-3.5 text-emerald-500 shrink-0" />
              <span>Standard resume matching & score analysis</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Check className="size-3.5 text-emerald-500 shrink-0" />
              <span>Deterministic form auto-fill</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground opacity-40">
              <X className="size-3.5 text-muted-foreground shrink-0" />
              <span className="line-through">Custom cover letter generator</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground opacity-40">
              <X className="size-3.5 text-muted-foreground shrink-0" />
              <span className="line-through">Big Tech ATS bypass optimization</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground opacity-40">
              <X className="size-3.5 text-muted-foreground shrink-0" />
              <span className="line-through">Interview questions & STAR answers</span>
            </div>
          </CardContent>
          <CardFooter className="pt-4 border-t border-border/50">
            <Button
              variant="outline"
              className="w-full text-xs font-semibold py-5"
              onClick={() => handleSelectPlan("free")}
            >
              Continue with Free (No Card Needed)
            </Button>
          </CardFooter>
        </Card>

        {/* GROWTH PLAN ($3.99) */}
        <Card
          className={`relative flex flex-col justify-between transition-all duration-200 hover:border-blue-500/80 ${
            selectedPlan === "starter" ? "border-blue-500 ring-2 ring-blue-500/20 shadow-lg" : "border-border/80"
          }`}
        >
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <Badge className="bg-blue-600 text-white hover:bg-blue-600 text-[10px] font-semibold tracking-wide shadow-sm">
              MOST POPULAR FOR INTERNS
            </Badge>
          </div>
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-xs text-blue-500 border-blue-500/30">Growth Tier</Badge>
            </div>
            <CardTitle className="text-xl font-bold mt-2">Growth Plan</CardTitle>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-3xl font-extrabold text-blue-500">$3.99</span>
              <span className="text-xs text-muted-foreground">/ month</span>
            </div>
            <CardDescription className="text-xs">
              Tailored cover letters in your personal voice to double callback rates.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3.5 text-xs">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <Zap className="size-4 text-blue-500 shrink-0" />
              <span><strong>20–25 applications</strong> / day</span>
            </div>
            <div className="flex items-center gap-2 text-foreground font-semibold">
              <Sparkles className="size-3.5 text-blue-500 shrink-0" />
              <span>Style-Mimicking Cover Letter AI</span>
            </div>
            <p className="text-[11px] text-muted-foreground pl-5 -mt-2">
              Analyzes your own resume & cover letter writing sample to mirror your exact style, vocabulary, and tone.
            </p>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Check className="size-3.5 text-emerald-500 shrink-0" />
              <span>Dynamic Job Description requirement alignment</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Check className="size-3.5 text-emerald-500 shrink-0" />
              <span>All Free Tier features included</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground opacity-40">
              <X className="size-3.5 text-muted-foreground shrink-0" />
              <span className="line-through">Big Tech ATS bypass optimization</span>
            </div>
            <div className="flex items-center gap-2 text-muted-foreground opacity-40">
              <X className="size-3.5 text-muted-foreground shrink-0" />
              <span className="line-through">Interview questions & STAR answers</span>
            </div>
          </CardContent>
          <CardFooter className="pt-4 border-t border-border/50">
            <Button
              className="w-full text-xs font-semibold py-5 bg-blue-600 hover:bg-blue-700 text-white gap-2 shadow-sm"
              onClick={() => handleSelectPlan("starter")}
            >
              <CreditCard className="size-3.5" /> Select Growth ($3.99)
            </Button>
          </CardFooter>
        </Card>

        {/* PRO PLAN ($7.99) */}
        <Card
          className={`relative flex flex-col justify-between transition-all duration-200 hover:border-emerald-500/80 ${
            selectedPlan === "pro" ? "border-emerald-500 ring-2 ring-emerald-500/20 shadow-xl" : "border-border/80"
          }`}
        >
          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
            <Badge className="bg-emerald-600 text-white hover:bg-emerald-600 text-[10px] font-semibold tracking-wide flex items-center gap-1 shadow-sm">
              <Star className="size-3 fill-white" /> BEST VALUE / 10X INTERVIEWS
            </Badge>
          </div>
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="outline" className="text-xs text-emerald-500 border-emerald-500/30">Pro Powerhouse</Badge>
            </div>
            <CardTitle className="text-xl font-bold mt-2">Pro Tier</CardTitle>
            <div className="mt-2 flex items-baseline gap-1">
              <span className="text-3xl font-extrabold text-emerald-500">$7.99</span>
              <span className="text-xs text-muted-foreground">/ month</span>
            </div>
            <CardDescription className="text-xs">
              Complete autonomous search: per-job tailored resumes, ATS bypass & interview coaching.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3.5 text-xs">
            <div className="flex items-center gap-2 font-medium text-foreground">
              <Zap className="size-4 text-emerald-500 shrink-0" />
              <span><strong>50 applications</strong> / day</span>
            </div>
            <div className="flex items-center gap-2 text-foreground font-semibold">
              <ShieldCheck className="size-3.5 text-emerald-500 shrink-0" />
              <span>Big Tech ATS Checker Bypass</span>
            </div>
            <p className="text-[11px] text-muted-foreground pl-5 -mt-2">
              Formats clean single-column parsable PDF/DOCX layouts that defeat Workday, Greenhouse & Taleo filters.
            </p>
            <div className="flex items-center gap-2 text-foreground font-semibold">
              <FileCheck className="size-3.5 text-emerald-500 shrink-0" />
              <span>Per-Job Customized Master Resume</span>
            </div>
            <div className="flex items-center gap-2 text-foreground font-semibold">
              <Sparkles className="size-3.5 text-emerald-500 shrink-0" />
              <span>Style-Mimicking Cover Letter AI</span>
            </div>
            <div className="flex items-center gap-2 text-foreground font-semibold">
              <Star className="size-3.5 text-emerald-500 shrink-0" />
              <span>Interview Guidance & Probable Q&A</span>
            </div>
            <p className="text-[11px] text-muted-foreground pl-5 -mt-2">
              Role & company-specific technical and behavioral questions + STAR-method answers.
            </p>
            <div className="flex items-center gap-2 text-muted-foreground">
              <Check className="size-3.5 text-emerald-500 shrink-0" />
              <span>Priority browser bot execution queue</span>
            </div>
          </CardContent>
          <CardFooter className="pt-4 border-t border-border/50">
            <Button
              className="w-full text-xs font-semibold py-5 bg-emerald-600 hover:bg-emerald-700 text-white gap-2 shadow-md"
              onClick={() => handleSelectPlan("pro")}
            >
              <CreditCard className="size-3.5" /> Select Pro ($7.99)
            </Button>
          </CardFooter>
        </Card>
      </div>

      <div className="mt-8 text-center text-xs text-muted-foreground flex items-center justify-center gap-2">
        <Lock className="size-3.5 text-emerald-500" />
        <span>Payments securely processed with 256-bit encryption. Cancel anytime with one click.</span>
      </div>
    </div>
  );
}
