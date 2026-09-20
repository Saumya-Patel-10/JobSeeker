"use client";

import type { ReactElement } from "react";
import { ResponsiveContainer } from "recharts";

type ChartContainerProps = {
  height?: number;
  children: ReactElement;
  className?: string;
};

/** Fixed-height chart wrapper — avoids Recharts width/height -1 on first paint (SSR/hydration). */
export function ChartContainer({
  height = 224,
  children,
  className = "w-full min-w-0",
}: ChartContainerProps) {
  return (
    <div className={className} style={{ height, minHeight: height }}>
      <ResponsiveContainer width="100%" height={height} minWidth={0}>
        {children}
      </ResponsiveContainer>
    </div>
  );
}
