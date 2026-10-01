import { cn } from "@/lib/utils";

type Tone = "success" | "info" | "warning" | "neutral";

const toneClass: Record<Tone, string> = {
  success: "bg-success/10 text-success",
  info: "bg-info/10 text-info",
  warning: "bg-warning/15 text-warning",
  neutral: "bg-muted text-muted-foreground",
};

const rows: Array<{
  company: string;
  role: string;
  match: number;
  status: string;
  tone: Tone;
}> = [
  { company: "Northwind", role: "Frontend Engineer Intern", match: 94, status: "Applied", tone: "success" },
  { company: "Contoso Labs", role: "Software Engineer, AI", match: 88, status: "Tailoring", tone: "info" },
  { company: "Fabrikam", role: "Full Stack Engineer", match: 81, status: "Needs review", tone: "warning" },
  { company: "Acme Cloud", role: "Backend Engineer", match: 76, status: "Queued", tone: "neutral" },
];

/** Static, illustrative preview of the dashboard used on the landing page. */
export function ProductPreview({ className }: { className?: string }) {
  return (
    <div
      className={cn("rounded-2xl border border-border bg-card p-4 sm:p-5", className)}
      role="img"
      aria-label="Preview of the applications list with sample data"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold">Recent applications</p>
        <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
          <span className="size-1.5 rounded-full bg-success" />
          Auto-applying
        </span>
      </div>

      <div className="mt-4 space-y-2.5">
        {rows.map((row) => (
          <div
            key={row.company}
            className="flex items-center gap-3 rounded-xl border border-border/80 bg-background/60 px-3 py-2.5"
          >
            <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-secondary text-sm font-semibold">
              {row.company.charAt(0)}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium">{row.role}</p>
              <p className="truncate text-xs text-muted-foreground">{row.company}</p>
            </div>
            <span className="hidden rounded-full bg-accent px-2 py-0.5 text-xs font-medium text-accent-foreground sm:inline tabular">
              {row.match}% match
            </span>
            <span
              className={cn(
                "rounded-full px-2.5 py-0.5 text-xs font-medium whitespace-nowrap",
                toneClass[row.tone]
              )}
            >
              {row.status}
            </span>
          </div>
        ))}
      </div>

      <div className="mt-4 space-y-1.5">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>Applied today</span>
          <span className="tabular font-medium text-foreground">12 / 15</span>
        </div>
        <div className="h-1.5 overflow-hidden rounded-full bg-muted">
          <div className="h-full w-4/5 rounded-full bg-primary" />
        </div>
      </div>

      <p className="mt-3 text-[11px] text-muted-foreground">Sample data for illustration.</p>
    </div>
  );
}
