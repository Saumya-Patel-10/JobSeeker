import type * as React from "react";

import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  right?: React.ReactNode;
  className?: string;
}

export function PageHeader({ title, description, right, className }: PageHeaderProps) {
  return (
    <div
      className={cn(
        "mb-4 flex flex-wrap items-start justify-between gap-3 rounded-2xl border border-border/70 bg-card/40 p-4",
        className
      )}
    >
      <div>
        <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
        {description ? <p className="mt-1 text-sm text-muted-foreground">{description}</p> : null}
      </div>
      {right ? <div className="ml-auto">{right}</div> : null}
    </div>
  );
}
