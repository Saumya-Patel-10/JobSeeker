"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { ChartContainer } from "@/components/charts/chart-container"
import { PageHeader } from "@/components/layout/page-header"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAnalyticsSummary } from "@/hooks/use-console-queries"

const pieColors = [
  "var(--color-chart-1)",
  "var(--color-chart-2)",
  "var(--color-chart-3)",
  "var(--color-chart-4)",
  "var(--color-chart-5)",
]

const chartHeight = 288

export function AnalyticsPage() {
  const analytics = useAnalyticsSummary()

  return (
    <div className="space-y-4">
      <PageHeader
        title="Analytics Dashboard"
        description="Application funnel, ATS success rates, score trends, and source effectiveness."
      />

      <section className="grid gap-4 xl:grid-cols-2">
        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Application Funnel</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer height={chartHeight}>
              <BarChart data={analytics.data?.funnel ?? []}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="stage" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="var(--color-chart-1)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Source Effectiveness</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer height={chartHeight}>
              <PieChart>
                <Pie
                  data={analytics.data?.source_effectiveness ?? []}
                  dataKey="applications"
                  nameKey="source"
                  outerRadius={100}
                >
                  {(analytics.data?.source_effectiveness ?? []).map((entry, index) => (
                    <Cell key={entry.source} fill={pieColors[index % pieColors.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-2">
        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Score Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer height={chartHeight}>
              <BarChart data={analytics.data?.score_distribution ?? []}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="label" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="var(--color-chart-3)" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ChartContainer>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Timeline (14 days)</CardTitle>
          </CardHeader>
          <CardContent>
            <ChartContainer height={chartHeight}>
              <LineChart data={analytics.data?.timeline_14d ?? []}>
                <CartesianGrid strokeDasharray="3 3" strokeOpacity={0.2} />
                <XAxis dataKey="day" tick={{ fontSize: 11 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="jobs" stroke="var(--color-chart-2)" strokeWidth={2} />
                <Line
                  type="monotone"
                  dataKey="applications"
                  stroke="var(--color-chart-4)"
                  strokeWidth={2}
                />
                <Line
                  type="monotone"
                  dataKey="submitted"
                  stroke="var(--color-chart-5)"
                  strokeWidth={2}
                />
              </LineChart>
            </ChartContainer>
          </CardContent>
        </Card>
      </section>

      <Card className="panel">
        <CardHeader>
          <CardTitle className="text-sm">ATS Success Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {analytics.data?.source_effectiveness.map((source) => (
            <div key={source.source} className="rounded-lg border border-border/70 p-3">
              <div className="flex items-center justify-between">
                <p className="font-medium">{source.source}</p>
                <p className="text-sm text-muted-foreground">
                  {(source.submission_rate * 100).toFixed(1)}% submission rate
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                jobs {source.jobs} · applications {source.applications} · submitted {source.submitted}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
