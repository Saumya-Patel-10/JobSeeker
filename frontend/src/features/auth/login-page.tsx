"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Mail, Lock, ArrowRight, ShieldCheck, Sparkles, Bot } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

function GoogleIcon() {
  return (
    <svg className="size-4 shrink-0" viewBox="0 0 24 24">
      <path
        fill="#4285F4"
        d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.8-2.4 3.66v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.15z"
      />
      <path
        fill="#34A853"
        d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.94H1.27v3.14C3.26 21.34 7.33 24 12 24z"
      />
      <path
        fill="#FBBC05"
        d="M5.28 14.26c-.25-.72-.38-1.49-.38-2.26s.13-1.54.38-2.26V6.6H1.27C.46 8.22 0 10.05 0 12s.46 3.78 1.27 5.4l4.01-3.14z"
      />
      <path
        fill="#EA4335"
        d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.33 0 3.26 2.66 1.27 6.6l4.01 3.14c.95-2.84 3.6-4.99 6.72-4.99z"
      />
    </svg>
  );
}

export function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("saumya.patel@example.com");
  const [password, setPassword] = useState("••••••••••••");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error("Please enter your email and password.");
      return;
    }

    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      if (typeof window !== "undefined") {
        localStorage.setItem(
          "jobai_user",
          JSON.stringify({
            name: "Saumya Patel",
            email: email,
            signedIn: true,
            provider: "credentials"
          })
        );
      }
      toast.success("Welcome back! Signing you in...");
      // Check if user already has a plan selected
      const existingPlan = typeof window !== "undefined" ? localStorage.getItem("jobai_user_plan") : null;
      if (existingPlan) {
        router.push("/");
      } else {
        router.push("/select-plan");
      }
    }, 700);
  };

  const handleGoogleSignIn = () => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
      if (typeof window !== "undefined") {
        localStorage.setItem(
          "jobai_user",
          JSON.stringify({
            name: "Saumya Patel",
            email: "saumya.patel@gmail.com",
            signedIn: true,
            provider: "google"
          })
        );
      }
      toast.success("Successfully authenticated with Google!");
      router.push("/select-plan");
    }, 900);
  };

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="w-full max-w-md"
      >
        {/* Brand Header */}
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex size-12 items-center justify-center rounded-2xl bg-primary/10 text-primary shadow-inner">
            <Bot className="size-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">Sign in to Job Finding AI</h1>
          <p className="mt-1 text-xs text-muted-foreground">
            Your autonomous agent applying to jobs, internships, and opportunities
          </p>
        </div>

        <Card className="border-border/80 shadow-lg">
          <CardHeader className="space-y-1 pb-4">
            <CardTitle className="text-lg">Welcome back</CardTitle>
            <CardDescription className="text-xs">
              Choose your preferred sign-in method
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Google Sign In Button */}
            <Button
              type="button"
              variant="outline"
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full gap-2 text-xs font-medium py-5 border-border/80 hover:bg-muted/50"
            >
              <GoogleIcon />
              Continue with Google
            </Button>

            <div className="relative flex items-center justify-center text-xs">
              <span className="w-full border-t border-border/70" />
              <span className="relative bg-card px-2 text-[11px] uppercase tracking-wider text-muted-foreground">
                Or with email
              </span>
              <span className="w-full border-t border-border/70" />
            </div>

            {/* Email / Password Form */}
            <form onSubmit={handleLogin} className="space-y-3.5">
              <div className="space-y-1.5">
                <Label htmlFor="email" className="text-xs">
                  Email address
                </Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="you@domain.com"
                    className="pl-9 text-xs"
                    required
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <Label htmlFor="password" className="text-xs">
                    Password
                  </Label>
                  <a href="#" className="text-[11px] text-primary hover:underline">
                    Forgot password?
                  </a>
                </div>
                <div className="relative">
                  <Lock className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                  <Input
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="pl-9 text-xs"
                    required
                  />
                </div>
              </div>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full gap-2 text-xs font-semibold py-5 mt-2"
              >
                {isLoading ? (
                  <span className="flex items-center gap-2">
                    <Sparkles className="size-4 animate-spin" /> Verifying...
                  </span>
                ) : (
                  <>
                    Sign In <ArrowRight className="size-4" />
                  </>
                )}
              </Button>
            </form>
          </CardContent>
          <CardFooter className="flex flex-col gap-3 border-t border-border/60 pt-4 text-center text-xs text-muted-foreground">
            <p>
              Don&apos;t have an account yet?{" "}
              <Link href="/signup" className="font-semibold text-primary hover:underline">
                Sign up here
              </Link>
            </p>
            <div className="flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground/80">
              <ShieldCheck className="size-3.5 text-emerald-500" />
              <span>End-to-end encrypted session</span>
            </div>
          </CardFooter>
        </Card>
      </motion.div>
    </div>
  );
}
