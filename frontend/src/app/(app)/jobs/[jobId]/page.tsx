import { JobDetailPage } from "@/features/jobs/job-detail-page"

export default async function JobDetailRoute({
  params,
}: {
  params: Promise<{ jobId: string }>
}) {
  const { jobId } = await params
  const numericJobId = Number(jobId)
  return <JobDetailPage jobId={numericJobId} />
}
