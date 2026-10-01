import Link from "next/link";
import { Sparkles } from "lucide-react";

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
        "relative flex size-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-violet-600 text-white shadow-sm shadow-indigo-500/30 transition-transform duration-200 hover:scale-105",
        className
      )}
      aria-hidden="true"
    >
      <Sparkles className="size-4 text-white" />
    </span>
  );
}

export function Logo({ href = "/", className, markOnly = false }: LogoProps) {
  return (
    <Link
      href={href}
      className={cn(
        "group inline-flex items-center gap-2.5 font-semibold tracking-tight transition-opacity hover:opacity-95",
        className
      )}
      aria-label={appName}
    >
      <LogoMark />
      {markOnly ? null : (
        <span className="flex items-center gap-1.5 text-[15px] font-bold tracking-tight">
          <span className="bg-gradient-to-r from-foreground via-foreground/90 to-foreground/75 bg-clip-text text-transparent">
            {appName}
          </span>
          <span className="rounded-md bg-indigo-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-indigo-600 dark:bg-indigo-500/20 dark:text-indigo-400">
            PRO
          </span>
        </span>
      )}
    </Link>
  );
}
