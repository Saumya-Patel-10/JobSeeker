import { apiBaseUrl } from "@/lib/env";
import { apiFetch } from "@/services/api/client";
import type {
  AIActivityEntry,
  AIActivitySummary,
  AnalyticsSummary,
  ActivityEntry,
  ApprovalQueueItem,
  ApplicationDetail,
  BlacklistSuggestionView,
  DiscoverySchedulerStatus,
  RuntimeSnapshot,
  SourceHealthView,
  ApplicationSummary,
  BatchIngestResponse,
  BrowserHealthView,
  BrowserProfileView,
  AutomationEventView,
  AutomationOverview,
  AutomationSessionView,
  JobHuntStartRequest,
  JobHuntStatus,
  JobDiscoveryConfig,
  JobDetail,
  JobSummary,
  JobWorkspace,
  ResumeSummary,
  ScoreView,
  SearchResponse,
  SettingsBundle,
  SettingsSection,
  StatusResponse,
} from "@/types/api";

export const api = {
  status: () => apiFetch<StatusResponse>("/status"),

  jobs: (params?: { limit?: number; offset?: number; status?: string }) =>
    apiFetch<JobSummary[]>("/jobs", { query: params }),

  jobDetail: (jobId: number) => apiFetch<JobDetail>(`/jobs/${jobId}`),

  jobWorkspace: (jobId: number) => apiFetch<JobWorkspace>(`/jobs/${jobId}/workspace`),

  applications: (params?: { status?: string; limit?: number; offset?: number }) =>
    apiFetch<ApplicationSummary[]>("/applications", { query: params }),

  applicationDetail: (applicationId: number) =>
    apiFetch<ApplicationDetail>(`/applications/${applicationId}`),

  updateApplicationStatus: (
    applicationId: number,
    payload: { status: string; notes?: string | null; confirmation_text?: string | null }
  ) =>
    apiFetch<ApplicationDetail>(`/applications/${applicationId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),

  resumesForJob: (jobId: number) => apiFetch<ResumeSummary[]>(`/resumes/job/${jobId}`),

  resumeDetail: (resumeId: number) => apiFetch<ResumeSummary>(`/resumes/${resumeId}`),

  score: (jobId: number) => apiFetch<ScoreView>(`/scoring/${jobId}`),

  rescore: (jobId: number) =>
    apiFetch<ScoreView>(`/scoring/${jobId}/rescore`, { method: "POST" }),

  profile: () => apiFetch<Record<string, unknown>>("/profile"),

  updateProfile: (payload: Record<string, unknown>) =>
    apiFetch<Record<string, unknown>>("/profile", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  settings: () => apiFetch<SettingsBundle>("/settings"),

  updateSettings: (section: SettingsSection, data: Record<string, unknown>) =>
    apiFetch<SettingsBundle>(`/settings/${section}`, {
      method: "PUT",
      body: JSON.stringify({ data }),
    }),

  analyticsSummary: () => apiFetch<AnalyticsSummary>("/analytics/summary"),

  automationOverview: () => apiFetch<AutomationOverview>("/automation/overview"),

  automationSessions: (limit = 50) =>
    apiFetch<AutomationSessionView[]>("/automation/sessions", { query: { limit } }),

  automationEvents: (params?: { application_id?: number; limit?: number }) =>
    apiFetch<AutomationEventView[]>("/automation/events", { query: params }),

  aiActivity: (limit = 200) => apiFetch<AIActivityEntry[]>("/ai/activity", { query: { limit } }),

  aiSummary: (limit = 500) => apiFetch<AIActivitySummary>("/ai/summary", { query: { limit } }),

  browserProfiles: () => apiFetch<BrowserProfileView[]>("/browser/profiles"),

  browserHealth: () => apiFetch<BrowserHealthView>("/browser/health"),

  cloneBrowserProfile: (payload: {
    source_profile_name: string;
    target_name?: string;
    overwrite?: boolean;
  }) =>
    apiFetch<BrowserProfileView>("/browser/profiles/clone", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  setActiveBrowserProfile: (payload: {
    profile_source: "system" | "managed";
    profile_name: string;
    persistent_profile?: boolean;
    reuse_existing_session?: boolean;
    clone_system_profile_on_lock?: boolean;
  }) =>
    apiFetch<BrowserHealthView>("/browser/active", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),

  jobHuntStatus: () => apiFetch<JobHuntStatus>("/control-center/job-hunt/status"),

  startJobHunt: (payload: JobHuntStartRequest) =>
    apiFetch<JobHuntStatus>("/control-center/job-hunt/start", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  pauseJobHunt: () =>
    apiFetch<JobHuntStatus>("/control-center/job-hunt/pause", {
      method: "POST",
    }),

  resumeJobHunt: () =>
    apiFetch<JobHuntStatus>("/control-center/job-hunt/resume", {
      method: "POST",
    }),

  stopJobHunt: () =>
    apiFetch<JobHuntStatus>("/control-center/job-hunt/stop", {
      method: "POST",
    }),

  ingestUrls: (payload: { urls: string[] }) =>
    apiFetch<BatchIngestResponse>("/control-center/ingest", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  searchSources: (payload: { limit?: number; discovery: JobDiscoveryConfig; save_defaults?: boolean }) =>
    apiFetch<SearchResponse>("/control-center/search", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  controlCenterActivity: (limit = 120) =>
    apiFetch<ActivityEntry[]>("/control-center/activity", { query: { limit } }),

  runtimeSnapshot: () => apiFetch<RuntimeSnapshot>("/automation/runtime"),

  discoveryStatus: () =>
    apiFetch<DiscoverySchedulerStatus>("/automation/runtime/discovery/status"),

  pauseAutomation: () =>
    apiFetch<RuntimeSnapshot>("/automation/runtime/pause", { method: "POST" }),

  resumeAutomation: () =>
    apiFetch<RuntimeSnapshot>("/automation/runtime/resume", { method: "POST" }),

  stopAutomation: () =>
    apiFetch<RuntimeSnapshot>("/automation/runtime/stop", { method: "POST" }),

  pauseAllAutomation: () =>
    apiFetch<RuntimeSnapshot>("/automation/runtime/pause-all", { method: "POST" }),

  manualControl: () =>
    apiFetch<RuntimeSnapshot>("/automation/runtime/manual-control", { method: "POST" }),

  returnToAi: () =>
    apiFetch<RuntimeSnapshot>("/automation/runtime/return-to-ai", { method: "POST" }),

  startDiscovery: (payload: {
    limit?: number;
    discovery: JobDiscoveryConfig;
    save_defaults?: boolean;
    interval_minutes?: number;
  }) =>
    apiFetch<DiscoverySchedulerStatus>("/control-center/discovery/start", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  pauseDiscovery: () =>
    apiFetch<DiscoverySchedulerStatus>("/control-center/discovery/pause", { method: "POST" }),

  resumeDiscovery: () =>
    apiFetch<DiscoverySchedulerStatus>("/control-center/discovery/resume", { method: "POST" }),

  stopDiscovery: () =>
    apiFetch<DiscoverySchedulerStatus>("/control-center/discovery/stop", { method: "POST" }),

  sourceHealth: () => apiFetch<SourceHealthView[]>("/sources"),

  pendingApprovals: () => apiFetch<ApprovalQueueItem[]>("/approvals/pending"),

  approveCheckpoint: (id: number, submit = false) =>
    apiFetch<{ approved: boolean }>(`/approvals/${id}/approve?submit=${submit}`, {
      method: "POST",
    }),

  rejectCheckpoint: (id: number) =>
    apiFetch<{ rejected: boolean }>(`/approvals/${id}/reject`, { method: "POST" }),

  requestEditCheckpoint: (id: number) =>
    apiFetch<{ edit_requested: boolean }>(`/approvals/${id}/request-edit`, { method: "POST" }),

  openBrowserForCheckpoint: (id: number) =>
    apiFetch<{ session_id: string }>(`/approvals/${id}/open-browser`, { method: "POST" }),

  blacklistSuggestions: () => apiFetch<BlacklistSuggestionView[]>("/blacklist/suggestions"),

  approveBlacklistSuggestion: (id: number) =>
    apiFetch<{ approved: boolean }>(`/blacklist/suggestions/${id}/approve`, { method: "POST" }),

  rejectBlacklistSuggestion: (id: number) =>
    apiFetch<{ rejected: boolean }>(`/blacklist/suggestions/${id}/reject`, { method: "POST" }),

  screenshotUrl: (path: string) => {
    const name = path.split(/[/\\]/).pop() ?? path;
    return `${apiBaseUrl}/automation/runtime/screenshots/${encodeURIComponent(name)}`;
  },
};
