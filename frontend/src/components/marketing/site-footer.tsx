import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { appName } from "@/lib/env";

export function SiteFooter() {
  return (
    <footer className="border-t border-border/70">
      <div className="mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 px-5 py-10 sm:flex-row sm:items-center">
        <div className="space-y-2">
          <Logo />
          <p className="max-w-xs text-sm text-muted-foreground">
            A personal AI job-search assistant. Runs on your machine with your data.
          </p>
        </div>

        <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
          <Link href="/dashboard" className="hover:text-foreground">
            Dashboard
          </Link>
          <Link href="/jobs" className="hover:text-foreground">
            Jobs
          </Link>
          <Link href="/review-queue" className="hover:text-foreground">
            Applications
          </Link>
          <Link href="/settings" className="hover:text-foreground">
            Settings
          </Link>
        </nav>
      </div>
      <div className="border-t border-border/70 py-4 text-center text-xs text-muted-foreground">
        &copy; {new Date().getFullYear()} {appName}. Personal use.
      </div>
    </footer>
  );
}
