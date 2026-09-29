"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  CreditCard,
  Lock,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Sparkles,
  Zap,
  Star,
  Info,
  Check
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

function CheckoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const planParam = searchParams.get("plan") ?? "pro";
  const plan = planParam === "starter" ? "starter" : "pro";

  const planDetails = {
    starter: {
      name: "Growth Plan",
      price: "$3.99",
      numericPrice: 3.99,
      period: "per month",
      dailyLimit: 25,
      features: [
        "20–25 automated job applications per day",
        "Style-Mimicking Cover Letter AI engine",
        "Analyzes your personal writing sample & tone",
        "Dynamic JD requirement alignment",
        "Greenhouse, Lever & Workday form auto-fill"
      ]
    },
    pro: {
      name: "Pro Tier Powerhouse",
      price: "$7.99",
      numericPrice: 7.99,
      period: "per month",
      dailyLimit: 50,
      features: [
        "50 automated job applications per day",
        "Big Tech ATS Checker Bypass (clean single-column layouts)",
        "Per-Job Customized Master Resume tailoring",
        "Style-Mimicking Cover Letter AI engine",
        "Role & Company Interview Guidance + STAR Answers",
        "Priority Playwright bot execution queue"
      ]
    }
  }[plan];

  // Card payment form state
  const [cardName, setCardName] = useState("Saumya Patel");
  const [cardNumber, setCardNumber] = useState("4532 8921 7392 4819");
  const [expiry, setExpiry] = useState("12/28");
  const [cvc, setCvc] = useState("892");
  const [zipCode, setZipCode] = useState("94107");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    // Format card number with spaces every 4 digits
    const raw = e.target.value.replace(/\D/g, "").slice(0, 16);
    const formatted = raw.match(/.{1,4}/g)?.join(" ") ?? raw;
    setCardNumber(formatted);
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = e.target.value.replace(/\D/g, "").slice(0, 4);
    if (raw.length >= 3) {
      setExpiry(`${raw.slice(0, 2)}/${raw.slice(2)}`);
    } else {
      setExpiry(raw);
    }
  };

  const handlePay = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cardNumber || !expiry || !cvc || !cardName) {
      toast.error("Please fill out all card details.");
      return;
    }

    setIsProcessing(true);

    setTimeout(() => {
      setIsProcessing(false);
      // Save subscription info in localStorage
      if (typeof window !== "undefined") {
        localStorage.setItem("jobai_user_plan", plan);
        localStorage.setItem("jobai_payment_status", "paid");
      }
      toast.success(
        `Payment of ${planDetails.price} authorized! Your ${planDetails.name} is now active.`
      );
      // Redirect to Resume Upload & Verification step in Onboarding
      router.push("/onboarding?step=resume");
    }, 1200);
  };

  return (
    <div className="mx-auto max-w-4xl py-8 px-4">
      {/* Back button */}
      <div className="mb-6">
        <Link href="/select-plan">
          <Button variant="ghost" size="sm" className="text-xs gap-1.5 text-muted-foreground hover:text-foreground">
            <ArrowLeft className="size-3.5" /> Back to Plans
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-12">
        {/* LEFT COLUMN: ORDER SUMMARY */}
        <div className="md:col-span-5 space-y-4">
          <Card className="border-border/80 shadow-md">
            <CardHeader className="pb-3">
              <Badge variant="outline" className="w-fit text-xs font-semibold text-primary border-primary/30">
                Order Summary
              </Badge>
              <CardTitle className="text-xl font-bold mt-1">{planDetails.name}</CardTitle>
              <div className="flex items-baseline gap-1 mt-1">
                <span className="text-3xl font-extrabold text-foreground">{planDetails.price}</span>
                <span className="text-xs text-muted-foreground">{planDetails.period}</span>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-1 text-xs">
              <Separator />
              <div className="space-y-2">
                <span className="font-semibold text-foreground">Included Features:</span>
                {planDetails.features.map((feature, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-muted-foreground">
                    <Check className="size-3.5 text-emerald-500 shrink-0 mt-0.5" />
                    <span>{feature}</span>
                  </div>
                ))}
              </div>

              <Separator />

              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Subtotal</span>
                  <span>{planDetails.price}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Sales Tax (0%)</span>
                  <span>$0.00</span>
                </div>
                <div className="flex justify-between font-bold text-sm text-foreground pt-1 border-t border-border/60">
                  <span>Total Due Today</span>
                  <span className="text-primary">{planDetails.price}</span>
                </div>
              </div>
            </CardContent>
            <CardFooter className="pt-2 pb-4 text-[11px] text-muted-foreground flex items-center gap-1.5 bg-muted/20 border-t border-border/60">
              <ShieldCheck className="size-4 text-emerald-500 shrink-0" />
              <span>14-day money-back guarantee. Cancel anytime.</span>
            </CardFooter>
          </Card>
        </div>

        {/* RIGHT COLUMN: PAYMENT PORTAL */}
        <div className="md:col-span-7">
          <Card className="border-border/80 shadow-lg">
            <CardHeader className="pb-4">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <CreditCard className="size-5 text-primary" /> Payment Details
                </CardTitle>
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <Lock className="size-3 text-emerald-500" />
                  <span>256-Bit SSL Encrypted</span>
                </div>
              </div>
              <CardDescription className="text-xs">
                Enter your credit or debit card to activate your {planDetails.name}.
              </CardDescription>
            </CardHeader>

            <CardContent>
              <form onSubmit={handlePay} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="cardName" className="text-xs">
                    Cardholder Name
                  </Label>
                  <Input
                    id="cardName"
                    value={cardName}
                    onChange={(e) => setCardName(e.target.value)}
                    placeholder="Full name as shown on card"
                    className="text-xs"
                    required
                  />
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="cardNumber" className="text-xs flex items-center justify-between">
                    <span>Card Number</span>
                    <span className="text-[10px] text-muted-foreground">Visa, Mastercard, Amex</span>
                  </Label>
                  <div className="relative">
                    <CreditCard className="absolute left-3 top-2.5 size-4 text-muted-foreground" />
                    <Input
                      id="cardNumber"
                      value={cardNumber}
                      onChange={handleCardNumberChange}
                      placeholder="1234 5678 9012 3456"
                      className="pl-9 font-mono text-xs"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="expiry" className="text-xs">
                      Expiration Date
                    </Label>
                    <Input
                      id="expiry"
                      value={expiry}
                      onChange={handleExpiryChange}
                      placeholder="MM/YY"
                      className="font-mono text-xs"
                      required
                    />
                  </div>

                  <div className="space-y-1.5">
                    <Label htmlFor="cvc" className="text-xs flex items-center justify-between">
                      <span>CVC / CVV</span>
                      <span className="text-[10px] text-muted-foreground">3-4 digits</span>
                    </Label>
                    <Input
                      id="cvc"
                      type="password"
                      maxLength={4}
                      value={cvc}
                      onChange={(e) => setCvc(e.target.value.replace(/\D/g, ""))}
                      placeholder="•••"
                      className="font-mono text-xs"
                      required
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label htmlFor="zip" className="text-xs">
                    Billing ZIP / Postal Code
                  </Label>
                  <Input
                    id="zip"
                    value={zipCode}
                    onChange={(e) => setZipCode(e.target.value)}
                    placeholder="e.g. 94107"
                    className="text-xs"
                    required
                  />
                </div>

                <div className="pt-2">
                  <Button
                    type="submit"
                    disabled={isProcessing}
                    className="w-full gap-2 text-xs font-semibold py-5 bg-emerald-600 hover:bg-emerald-700 text-white shadow-md"
                  >
                    {isProcessing ? (
                      <span className="flex items-center gap-2">
                        <Sparkles className="size-4 animate-spin" /> Authorizing Payment...
                      </span>
                    ) : (
                      <>
                        <Lock className="size-3.5" /> Pay {planDetails.price} & Activate Plan
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </CardContent>

            <CardFooter className="flex flex-col gap-2 border-t border-border/60 pt-4 text-center text-xs text-muted-foreground bg-muted/10">
              <p className="text-[11px]">
                By confirming your payment, you agree to our Terms of Service and recurring monthly subscription. You can cancel at any time.
              </p>
            </CardFooter>
          </Card>
        </div>
      </div>
    </div>
  );
}

export function CheckoutPage() {
  return (
    <Suspense fallback={<div className="p-8 text-center text-xs text-muted-foreground">Loading payment portal...</div>}>
      <CheckoutContent />
    </Suspense>
  );
}
