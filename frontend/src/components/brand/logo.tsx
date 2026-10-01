import Link from "next/link";
import { Send } from "lucide-react";

import { appName } from "@/lib/env";
import { cn } from "@/lib/utils";

interface LogoProps {
  href?: string;
  className?: string;
  /** Hide the wordmark and render the mark only. */
  markOnly?: boolean;
}

export function LogoMark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground",
        className
      )}
      aria-hidden="true"
    >
      <Send className="size-4 -translate-x-px translate-y-px" />
    </span>
  );
}

export function Logo({ href = "/", className, markOnly = false }: LogoProps) {
  return (
    <Link
      href={href}
      className={cn("inline-flex items-center gap-2.5 font-semibold tracking-tight", className)}
      aria-label={appName}
    >
      <LogoMark />
      {markOnly ? null : <span className="text-[15px]">{appName}</span>}
    </Link>
  );
}
