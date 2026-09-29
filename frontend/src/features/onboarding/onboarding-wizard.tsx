"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Check,
  Upload,
  FileText,
  Sparkles,
  ShieldCheck,
  ArrowRight,
  ArrowLeft,
  User,
  Mail,
  Lock,
  CheckCircle2,
  Zap,
  Star,
  Building,
  GraduationCap,
  Globe,
  Briefcase,
  AlertCircle,
  Plus,
  X,
  FileCheck,
  CreditCard
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";

export type PlanType = "free" | "starter" | "pro";

interface ExtractedData {
  fullName: string;
  email: string;
  phone: string;
  location: string;
  linkedinUrl: string;
  githubUrl: string;
  portfolioUrl: string;
  targetRole: string;
  skills: string[];
  workAuthorization: "us_citizen" | "green_card" | "stem_opt" | "require_sponsor";
  yearsOfExperience: string;
  minSalary: string;
  remotePreference: "remote" | "hybrid" | "onsite" | "any";
  writingSample: string;
}

function OnboardingWizardContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [currentStep, setCurrentStep] = useState<number>(1); // 1: Account, 2: Plan, 3: Resume, 4: Verification

  useEffect(() => {
    const stepParam = searchParams.get("step");
    if (stepParam === "plan") {
      setCurrentStep(2);
    } else if (stepParam === "resume") {
      setCurrentStep(3);
    } else if (stepParam === "verification") {
      setCurrentStep(4);
    }

    if (typeof window !== "undefined") {
      const storedPlan = localStorage.getItem("jobai_user_plan") as PlanType;
      if (storedPlan) setSelectedPlan(storedPlan);
    }
  }, [searchParams]);

  // Step A: Account Form State
  const [accountData, setAccountData] = useState({
    firstName: "Saumya",
    lastName: "Patel",
    email: "saumya.patel@example.com",
    password: "••••••••••••",
    agreedToTerms: true,
  });

  // Step B: Plan State
  const [selectedPlan, setSelectedPlan] = useState<PlanType>("pro");

  // Step C: Resume Upload State
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isParsing, setIsParsing] = useState<boolean>(false);
  const [parsingProgress, setParsingProgress] = useState<string>("Ready to upload");

  // Step D: Extracted Data / Verification State
  const [extractedData, setExtractedData] = useState<ExtractedData>({
    fullName: "Saumya Patel",
    email: "saumya.patel@example.com",
    phone: "+1 (555) 382-9912",
    location: "San Francisco, CA (Open to Relocate)",
    linkedinUrl: "https://linkedin.com/in/saumyapatel",
    githubUrl: "https://github.com/saumya-patel",
    portfolioUrl: "https://saumyapatel.dev",
    targetRole: "Full Stack Engineer / AI Systems",
    skills: [
      "TypeScript",
      "React",
      "Next.js",
      "Python",
      "FastAPI",
      "Tailwind CSS",
      "Playwright",
      "PostgreSQL",
      "Docker",
      "OpenAI API",
      "Celery",
      "Redis"
    ],
    workAuthorization: "us_citizen",
    yearsOfExperience: "2+ Years / New Grad",
    minSalary: "$110,000",
    remotePreference: "any",
    writingSample:
      "I am passionate about building autonomous web agents and robust full-stack software. I enjoy taking complex workflows, distilling them into deterministic browser automations, and pairing them with LLM reasoning."
  });

  const [newSkillInput, setNewSkillInput] = useState("");

  const handleStepBNext = () => {
    if (selectedPlan === "free") {
      if (typeof window !== "undefined") {
        localStorage.setItem("jobai_user_plan", "free");
      }
      toast.success("Free plan selected! Upload your resume next.");
      setCurrentStep(3);
    } else {
      toast.info(`Redirecting to payment portal for ${selectedPlan === "starter" ? "$3.99 Growth" : "$7.99 Pro"} plan...`);
      router.push(`/checkout?plan=${selectedPlan}`);
    }
  };

  // Handle Mock Upload & Extraction Animation
  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      simulateParsing(file.name);
    }
  };

  const simulateParsing = (fileName: string) => {
    setIsParsing(true);
    setParsingProgress("Reading PDF layout & text layers...");

    setTimeout(() => {
      setParsingProgress("Extracting contact details & links...");
    }, 900);

    setTimeout(() => {
      setParsingProgress("Classifying work experience & technical skills...");
    }, 1800);

    setTimeout(() => {
      setParsingProgress("Optimizing for Big Tech ATS schemas...");
    }, 2600);

    setTimeout(() => {
      setIsParsing(false);
      toast.success("Resume parsed successfully!");
      setCurrentStep(4); // Advance to Human-in-the-loop review
    }, 3400);
  };

  const handleAddSkill = () => {
    if (newSkillInput.trim() && !extractedData.skills.includes(newSkillInput.trim())) {
      setExtractedData({
        ...extractedData,
        skills: [...extractedData.skills, newSkillInput.trim()]
      });
      setNewSkillInput("");
    }
  };

  const handleRemoveSkill = (skillToRemove: string) => {
    setExtractedData({
      ...extractedData,
      skills: extractedData.skills.filter((s) => s !== skillToRemove)
    });
  };

  const handleCompleteOnboarding = () => {
    // Save onboarding preferences to localStorage for instant local demo resilience
    if (typeof window !== "undefined") {
      localStorage.setItem("jobai_user_plan", selectedPlan);
      localStorage.setItem("jobai_user_profile", JSON.stringify(extractedData));
      localStorage.setItem("jobai_onboarding_completed", "true");
    }
    toast.success("Onboarding complete! Welcome to the Command Center.");
    router.push("/");
  };

  const steps = [
    { num: 1, label: "Account Creation", sub: "Basic credentials" },
    { num: 2, label: "Plan Selection", sub: "Quota & features" },
    { num: 3, label: "Resume Upload", sub: "AI extraction" },
    { num: 4, label: "Data Verification", sub: "Human-in-the-loop" }
  ];

  return (
    <div className="mx-auto max-w-5xl py-6 px-4">
      {/* Step Progress Tracker */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Job Finding AI Setup</h1>
            <p className="text-sm text-muted-foreground">
              Setup your autonomous job-seeking agent in 4 simple steps
            </p>
          </div>
          <Badge variant="outline" className="px-3 py-1 text-xs font-semibold bg-primary/10 text-primary border-primary/30">
            Step {currentStep} of 4: {steps[currentStep - 1].label}
          </Badge>
        </div>

        {/* Stepper bar */}
        <div className="mt-6 grid grid-cols-4 gap-2 sm:gap-4">
          {steps.map((s) => {
            const isDone = currentStep > s.num;
            const isCurrent = currentStep === s.num;
            return (
              <div
                key={s.num}
                onClick={() => {
                  if (isDone) setCurrentStep(s.num);
                }}
                className={`relative flex flex-col border-t-2 pt-2 cursor-pointer transition-colors ${
                  isCurrent
                    ? "border-primary text-primary"
                    : isDone
                    ? "border-emerald-500 text-foreground"
                    : "border-border text-muted-foreground"
                }`}
              >
                <div className="flex items-center gap-1.5 text-xs font-medium">
                  {isDone ? (
                    <CheckCircle2 className="size-3.5 text-emerald-500" />
                  ) : (
                    <span
                      className={`flex size-4 items-center justify-center rounded-full text-[10px] ${
                        isCurrent ? "bg-primary text-primary-foreground font-bold" : "bg-muted"
                      }`}
                    >
                      {s.num}
                    </span>
                  )}
                  <span className="truncate">{s.label}</span>
                </div>
                <span className="hidden sm:inline text-[11px] text-muted-foreground truncate">{s.sub}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Main Wizard Step Content with Animation */}
      <AnimatePresence mode="wait">
        {/* STEP A: ACCOUNT CREATION */}
        {currentStep === 1 && (
          <motion.div
            key="step1"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="border-border/80 shadow-md">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="rounded-lg bg-primary/10 p-2 text-primary">
                    <User className="size-5" />
                  </div>
                  <div>
                    <CardTitle>Create your Candidate Account</CardTitle>
                    <CardDescription>
                      Sign up to let your AI assistant monitor openings, tailor your applications, and apply for you.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="firstName">First Name</Label>
                    <Input
                      id="firstName"
                      value={accountData.firstName}
                      onChange={(e) => setAccountData({ ...accountData, firstName: e.target.value })}
                      placeholder="e.g. Alex"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="lastName">Last Name</Label>
                    <Input
                      id="lastName"
                      value={accountData.lastName}
                      onChange={(e) => setAccountData({ ...accountData, lastName: e.target.value })}
                      placeholder="e.g. Chen"
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="email">Email Address</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                    <Input
                      id="email"
                      type="email"
                      className="pl-9"
                      value={accountData.email}
                      onChange={(e) => setAccountData({ ...accountData, email: e.target.value })}
                      placeholder="you@domain.com"
                    />
                  </div>
                  <p className="text-[11px] text-muted-foreground">
                    This email will be used on job forms (Greenhouse, Lever, Workday) and for confirmation notifications.
                  </p>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="password">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                    <Input
                      id="password"
                      type="password"
                      className="pl-9"
                      value={accountData.password}
                      onChange={(e) => setAccountData({ ...accountData, password: e.target.value })}
                      placeholder="••••••••••••"
                    />
                  </div>
                </div>

                <div className="pt-2">
                  <label className="flex items-center gap-2 cursor-pointer text-xs text-muted-foreground">
                    <input
                      type="checkbox"
                      checked={accountData.agreedToTerms}
                      onChange={(e) => setAccountData({ ...accountData, agreedToTerms: e.target.checked })}
                      className="rounded border-border text-primary focus:ring-primary"
                    />
                    I agree to allow the AI agent to prepare job applications on my behalf under my supervision.
                  </label>
                </div>
              </CardContent>
              <CardFooter className="flex justify-between border-t border-border/60 pt-4">
                <div className="text-xs text-muted-foreground flex items-center gap-1.5">
                  <ShieldCheck className="size-4 text-emerald-500" />
                  <span>256-bit encrypted credentials</span>
                </div>
                <Button onClick={() => setCurrentStep(2)} className="gap-2">
                  Continue to Plan Selection <ArrowRight className="size-4" />
                </Button>
              </CardFooter>
            </Card>
          </motion.div>
        )}

        {/* STEP B: PLAN SELECTION */}
        {currentStep === 2 && (
          <motion.div
            key="step2"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
          >
            <div className="mb-4 text-center">
              <h2 className="text-xl font-bold">Choose your AI Automation Plan</h2>
              <p className="text-sm text-muted-foreground">
                Select your daily application volume and AI tailoring features. You can upgrade or downgrade anytime.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {/* FREE PLAN */}
              <Card
                onClick={() => setSelectedPlan("free")}
                className={`relative cursor-pointer transition-all duration-200 hover:border-primary/80 ${
                  selectedPlan === "free" ? "border-primary ring-2 ring-primary/20 shadow-lg bg-card/95" : "border-border/70"
                }`}
              >
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">Entry Level</Badge>
                    {selectedPlan === "free" && <CheckCircle2 className="size-5 text-primary" />}
                  </div>
                  <CardTitle className="text-xl font-bold">Free Plan</CardTitle>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold">$0</span>
                    <span className="text-xs text-muted-foreground">/ month</span>
                  </div>
                  <CardDescription className="text-xs">
                    Great for casually testing the job auto-apply agent.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <div className="flex items-center gap-2 font-medium text-foreground">
                    <Zap className="size-4 text-primary shrink-0" />
                    <span><strong>10–15 applications</strong> / day</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Automatic job radar & opening detection</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Standard resume matching & scoring</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Greenhouse & Lever auto-fill support</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground opacity-40">
                    <X className="size-3.5 text-muted-foreground shrink-0" />
                    <span className="line-through">Custom cover letter generator</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground opacity-40">
                    <X className="size-3.5 text-muted-foreground shrink-0" />
                    <span className="line-through">Big Tech ATS bypass optimization</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-2">
                  <Button
                    variant={selectedPlan === "free" ? "default" : "outline"}
                    className="w-full text-xs"
                    onClick={() => setSelectedPlan("free")}
                  >
                    {selectedPlan === "free" ? "Selected Plan" : "Choose Free"}
                  </Button>
                </CardFooter>
              </Card>

              {/* STARTER / GROWTH PLAN ($3.99) */}
              <Card
                onClick={() => setSelectedPlan("starter")}
                className={`relative cursor-pointer transition-all duration-200 hover:border-primary/80 ${
                  selectedPlan === "starter"
                    ? "border-primary ring-2 ring-primary/20 shadow-lg bg-card/95"
                    : "border-border/70"
                }`}
              >
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-blue-600 text-white hover:bg-blue-600 text-[10px] font-semibold tracking-wide">
                    POPULAR FOR INTERNSHIPS
                  </Badge>
                </div>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs text-blue-500 border-blue-500/30">Growth Tier</Badge>
                    {selectedPlan === "starter" && <CheckCircle2 className="size-5 text-primary" />}
                  </div>
                  <CardTitle className="text-xl font-bold">Growth</CardTitle>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold">$3.99</span>
                    <span className="text-xs text-muted-foreground">/ month</span>
                  </div>
                  <CardDescription className="text-xs">
                    Accelerate your search with tailored cover letters in your voice.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <div className="flex items-center gap-2 font-medium text-foreground">
                    <Zap className="size-4 text-blue-500 shrink-0" />
                    <span><strong>20–25 applications</strong> / day</span>
                  </div>
                  <div className="flex items-center gap-2 text-foreground font-semibold">
                    <Sparkles className="size-3.5 text-blue-500 shrink-0" />
                    <span>Style-Mimicking Cover Letter AI</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground pl-5 -mt-1.5">
                    Analyzes your writing sample to match your exact tone and vocabulary per job.
                  </p>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Dynamic Job Description alignment</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                    <span>All Free Tier features included</span>
                  </div>
                  <div className="flex items-center gap-2 text-muted-foreground opacity-40">
                    <X className="size-3.5 text-muted-foreground shrink-0" />
                    <span className="line-through">Big Tech ATS bypass optimization</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-2">
                  <Button
                    variant={selectedPlan === "starter" ? "default" : "outline"}
                    className="w-full text-xs"
                    onClick={() => setSelectedPlan("starter")}
                  >
                    {selectedPlan === "starter" ? "Selected Plan" : "Choose Growth ($3.99)"}
                  </Button>
                </CardFooter>
              </Card>

              {/* PRO PLAN ($7.99) */}
              <Card
                onClick={() => setSelectedPlan("pro")}
                className={`relative cursor-pointer transition-all duration-200 hover:border-primary/80 ${
                  selectedPlan === "pro"
                    ? "border-emerald-500 ring-2 ring-emerald-500/20 shadow-lg bg-card/95"
                    : "border-border/70"
                }`}
              >
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <Badge className="bg-emerald-600 text-white hover:bg-emerald-600 text-[10px] font-semibold tracking-wide flex items-center gap-1">
                    <Star className="size-3 fill-white" /> BEST VALUE / 10X INTERVIEWS
                  </Badge>
                </div>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs text-emerald-500 border-emerald-500/30">Pro Powerhouse</Badge>
                    {selectedPlan === "pro" && <CheckCircle2 className="size-5 text-emerald-500" />}
                  </div>
                  <CardTitle className="text-xl font-bold">Pro Tier</CardTitle>
                  <div className="mt-2 flex items-baseline gap-1">
                    <span className="text-3xl font-extrabold text-emerald-500">$7.99</span>
                    <span className="text-xs text-muted-foreground">/ month</span>
                  </div>
                  <CardDescription className="text-xs">
                    Full autonomous power: per-job tailored resumes, ATS bypass & interview prep.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-3 text-xs">
                  <div className="flex items-center gap-2 font-medium text-foreground">
                    <Zap className="size-4 text-emerald-500 shrink-0" />
                    <span><strong>50 applications</strong> / day</span>
                  </div>
                  <div className="flex items-center gap-2 text-foreground font-semibold">
                    <ShieldCheck className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Big Tech ATS Checker Bypass</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground pl-5 -mt-1.5">
                    Single-column clean parsing layout + semantic keyword density for Workday/Greenhouse.
                  </p>
                  <div className="flex items-center gap-2 text-foreground font-semibold">
                    <FileCheck className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Per-Job Customized Master Resume</span>
                  </div>
                  <div className="flex items-center gap-2 text-foreground font-semibold">
                    <Sparkles className="size-3.5 text-emerald-500 shrink-0" />
                    <span>Role & Company Interview Q&A Guide</span>
                  </div>
                  <p className="text-[11px] text-muted-foreground pl-5 -mt-1.5">
                    Unlocks probable technical/behavioral questions + STAR answer frameworks.
                  </p>
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0" />
                    <span>All $3.99 & Free features included</span>
                  </div>
                </CardContent>
                <CardFooter className="pt-2">
                  <Button
                    variant={selectedPlan === "pro" ? "default" : "outline"}
                    className="w-full text-xs bg-emerald-600 hover:bg-emerald-700 text-white"
                    onClick={() => setSelectedPlan("pro")}
                  >
                    {selectedPlan === "pro" ? "Selected Plan" : "Choose Pro ($7.99)"}
                  </Button>
                </CardFooter>
              </Card>
            </div>

            <div className="mt-6 flex justify-between border-t border-border/60 pt-4">
              <Button variant="outline" onClick={() => setCurrentStep(1)} className="gap-2">
                <ArrowLeft className="size-4" /> Back to Account
              </Button>
              <Button onClick={handleStepBNext} className="gap-2">
                {selectedPlan === "free" ? (
                  <>Continue to Resume Upload <ArrowRight className="size-4" /></>
                ) : (
                  <><CreditCard className="size-4" /> Proceed to Payment ({selectedPlan === "starter" ? "$3.99" : "$7.99"})</>
                )}
              </Button>
            </div>
          </motion.div>
        )}

        {/* STEP C: RESUME UPLOAD & AI PARSING */}
        {currentStep === 3 && (
          <motion.div
            key="step3"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
          >
            <Card className="border-border/80 shadow-md">
              <CardHeader>
                <div className="flex items-center gap-2">
                  <div className="rounded-lg bg-primary/10 p-2 text-primary">
                    <Upload className="size-5" />
                  </div>
                  <div>
                    <CardTitle>Upload your Master Resume</CardTitle>
                    <CardDescription>
                      Upload your PDF or Word DOCX resume. Our AI model will extract your work experience, education, and skills.
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Drag and Drop Zone */}
                <div className="relative flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-border/80 bg-muted/20 p-8 text-center transition-colors hover:border-primary hover:bg-primary/5">
                  <input
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    className="absolute inset-0 z-10 cursor-pointer opacity-0"
                    disabled={isParsing}
                  />
                  <div className="mb-3 rounded-full bg-primary/10 p-4 text-primary">
                    <FileText className="size-8" />
                  </div>
                  <h3 className="text-base font-semibold">
                    {uploadedFile ? uploadedFile.name : "Click or drag your resume here"}
                  </h3>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Supports PDF, DOCX (Max 10MB). Clean ATS-compatible format recommended.
                  </p>

                  <div className="mt-4 flex gap-2">
                    <Button variant="secondary" size="sm" className="pointer-events-none text-xs">
                      Choose File
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="text-xs"
                      onClick={(e) => {
                        e.stopPropagation();
                        simulateParsing("Master_Resume_Saumya_Patel.pdf");
                      }}
                    >
                      Use Demo Resume
                    </Button>
                  </div>
                </div>

                {/* Parsing Progress / Scanner Display */}
                {isParsing && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    className="rounded-lg border border-primary/40 bg-primary/5 p-4 space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-primary flex items-center gap-2">
                        <Sparkles className="size-4 animate-spin text-primary" />
                        AI Resume Extraction Engine Running
                      </span>
                      <span className="text-muted-foreground">Gemini & PyPDF parser</span>
                    </div>

                    <div className="h-2 w-full overflow-hidden rounded-full bg-primary/20">
                      <motion.div
                        className="h-full bg-primary"
                        initial={{ width: "10%" }}
                        animate={{ width: "95%" }}
                        transition={{ duration: 3.2, ease: "easeInOut" }}
                      />
                    </div>

                    <p className="text-xs text-muted-foreground animate-pulse">{parsingProgress}</p>
                  </motion.div>
                )}
              </CardContent>
              <CardFooter className="flex justify-between border-t border-border/60 pt-4">
                <Button variant="outline" onClick={() => setCurrentStep(2)} className="gap-2">
                  <ArrowLeft className="size-4" /> Back to Plans
                </Button>
                <Button
                  onClick={() => setCurrentStep(4)}
                  disabled={isParsing}
                  className="gap-2"
                >
                  Continue to Verification <ArrowRight className="size-4" />
                </Button>
              </CardFooter>
            </Card>
          </motion.div>
        )}

        {/* STEP D: DATA VERIFICATION (HUMAN-IN-THE-LOOP SCREEN) */}
        {currentStep === 4 && (
          <motion.div
            key="step4"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.2 }}
            className="space-y-6"
          >
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 p-3.5 flex items-start gap-3">
              <CheckCircle2 className="size-5 text-emerald-500 shrink-0 mt-0.5" />
              <div className="text-xs">
                <p className="font-semibold text-emerald-500">Human-In-The-Loop Data Confirmation</p>
                <p className="text-muted-foreground mt-0.5">
                  Please review and confirm the details extracted from your resume. These answers will be automatically populated into job application forms (Greenhouse, Lever, Workday) by the Playwright bot.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              {/* Personal & Contact Details */}
              <Card className="border-border/80">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <User className="size-4 text-primary" /> Contact & Location Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Full Name</Label>
                    <Input
                      value={extractedData.fullName}
                      onChange={(e) => setExtractedData({ ...extractedData, fullName: e.target.value })}
                      className="text-xs"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label className="text-xs">Email</Label>
                      <Input
                        value={extractedData.email}
                        onChange={(e) => setExtractedData({ ...extractedData, email: e.target.value })}
                        className="text-xs"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Phone Number</Label>
                      <Input
                        value={extractedData.phone}
                        onChange={(e) => setExtractedData({ ...extractedData, phone: e.target.value })}
                        className="text-xs"
                      />
                    </div>
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Current Location</Label>
                    <Input
                      value={extractedData.location}
                      onChange={(e) => setExtractedData({ ...extractedData, location: e.target.value })}
                      className="text-xs"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Work Authorization & Legal Questions */}
              <Card className="border-border/80">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <ShieldCheck className="size-4 text-primary" /> Work Authorization & Visa Details
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <Label className="text-xs">Are you legally authorized to work in the country?</Label>
                    <select
                      value={extractedData.workAuthorization}
                      onChange={(e) =>
                        setExtractedData({
                          ...extractedData,
                          workAuthorization: e.target.value as ExtractedData["workAuthorization"]
                        })
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground shadow-sm"
                    >
                      <option value="us_citizen">Yes — US Citizen / Permanent Resident</option>
                      <option value="green_card">Yes — Green Card Holder</option>
                      <option value="stem_opt">Yes — F-1 STEM OPT (Valid EAD)</option>
                      <option value="require_sponsor">No — Will require Visa Sponsorship (H-1B)</option>
                    </select>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="space-y-1">
                      <Label className="text-xs">Target Role</Label>
                      <Input
                        value={extractedData.targetRole}
                        onChange={(e) => setExtractedData({ ...extractedData, targetRole: e.target.value })}
                        className="text-xs"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Minimum Base Salary</Label>
                      <Input
                        value={extractedData.minSalary}
                        onChange={(e) => setExtractedData({ ...extractedData, minSalary: e.target.value })}
                        className="text-xs"
                      />
                    </div>
                  </div>

                  <div className="space-y-1">
                    <Label className="text-xs">Workplace Preference</Label>
                    <select
                      value={extractedData.remotePreference}
                      onChange={(e) =>
                        setExtractedData({
                          ...extractedData,
                          remotePreference: e.target.value as ExtractedData["remotePreference"]
                        })
                      }
                      className="w-full rounded-md border border-input bg-background px-3 py-1.5 text-xs text-foreground shadow-sm"
                    >
                      <option value="any">Open to Any (Remote, Hybrid, or On-site)</option>
                      <option value="remote">Remote Only</option>
                      <option value="hybrid">Hybrid</option>
                      <option value="onsite">On-site</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              {/* Web Profiles & Links */}
              <Card className="border-border/80">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Globe className="size-4 text-primary" /> Portfolio & Profiles
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="space-y-1">
                    <Label className="text-xs">LinkedIn Profile</Label>
                    <Input
                      value={extractedData.linkedinUrl}
                      onChange={(e) => setExtractedData({ ...extractedData, linkedinUrl: e.target.value })}
                      className="text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">GitHub Profile</Label>
                    <Input
                      value={extractedData.githubUrl}
                      onChange={(e) => setExtractedData({ ...extractedData, githubUrl: e.target.value })}
                      className="text-xs"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label className="text-xs">Personal Website / Portfolio</Label>
                    <Input
                      value={extractedData.portfolioUrl}
                      onChange={(e) => setExtractedData({ ...extractedData, portfolioUrl: e.target.value })}
                      className="text-xs"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Skills Verification & Tag Manager */}
              <Card className="border-border/80">
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm font-semibold flex items-center gap-2">
                    <Sparkles className="size-4 text-primary" /> Extracted Skills ({extractedData.skills.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Add a new skill (e.g. AWS, PyTorch)"
                      value={newSkillInput}
                      onChange={(e) => setNewSkillInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter") {
                          e.preventDefault();
                          handleAddSkill();
                        }
                      }}
                      className="text-xs"
                    />
                    <Button size="sm" variant="secondary" onClick={handleAddSkill} className="text-xs">
                      <Plus className="size-3.5 mr-1" /> Add
                    </Button>
                  </div>

                  <div className="flex flex-wrap gap-1.5 max-h-36 overflow-y-auto pr-1">
                    {extractedData.skills.map((skill) => (
                      <Badge
                        key={skill}
                        variant="secondary"
                        className="text-[11px] gap-1 px-2 py-0.5 bg-muted hover:bg-muted/80"
                      >
                        {skill}
                        <button
                          type="button"
                          onClick={() => handleRemoveSkill(skill)}
                          className="hover:text-destructive transition-colors ml-0.5"
                        >
                          <X className="size-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Writing Sample Calibration (for $3.99 & $7.99 plans) */}
            {(selectedPlan === "starter" || selectedPlan === "pro") && (
              <Card className="border-blue-500/40 bg-blue-500/5">
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm font-semibold flex items-center gap-2 text-blue-500">
                      <Sparkles className="size-4" /> AI Cover Letter Voice Calibration
                    </CardTitle>
                    <Badge variant="outline" className="text-[10px] text-blue-500 border-blue-500/30">
                      Enabled on {selectedPlan === "pro" ? "$7.99 Pro" : "$3.99 Growth"} Plan
                    </Badge>
                  </div>
                  <CardDescription className="text-xs">
                    Paste a brief sample of your past writing or cover letter. The AI model will analyze your vocabulary and sentence cadence to generate matching cover letters.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    rows={3}
                    value={extractedData.writingSample}
                    onChange={(e) => setExtractedData({ ...extractedData, writingSample: e.target.value })}
                    className="text-xs bg-background/80"
                    placeholder="Paste a paragraph from a cover letter or bio that reflects your authentic tone..."
                  />
                </CardContent>
              </Card>
            )}

            <div className="flex justify-between border-t border-border/60 pt-4">
              <Button variant="outline" onClick={() => setCurrentStep(3)} className="gap-2">
                <ArrowLeft className="size-4" /> Back to Resume
              </Button>
              <Button
                onClick={handleCompleteOnboarding}
                className="gap-2 bg-emerald-600 hover:bg-emerald-700 text-white shadow-md"
              >
                <Check className="size-4" /> Confirm & Launch Command Center
              </Button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function OnboardingWizard() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-muted-foreground">Loading onboarding wizard...</div>}>
      <OnboardingWizardContent />
    </Suspense>
  );
}
