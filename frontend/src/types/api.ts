export type ISODateTime = string;

export interface StatusResponse {
  healthy: boolean;
  llm_provider: string;
  llm_reachable: boolean;
  llm_base_url: string;
  db_path: string;
  db_exists: boolean;
  apply_default_mode: string;
  allow_auto_submit: boolean;
  browser_engine: string;
  browser_headless: boolean;
  browser_persistent_profile: boolean;
  browser_profile_source: string;
  browser_profile_name: string | null;
  browser_profile_path: string | null;
  browser_profile_exists: boolean;
  browser_profile_locked: boolean;
  browser_profile_has_cookies: boolean;
  firefox_profiles_detected: number;
  managed_browser_profiles_detected: number;
}

export interface BrowserProfileView {
  name: string;
  path: string;
  source: "system" | "managed";
  is_default: boolean;
  exists: boolean;
  has_prefs: boolean;
  has_cookies_db: boolean;
  locked: boolean;
}

export interface BrowserHealthView {
  engine: string;
  headless: boolean;
  persistent_profile: boolean;
  profile_source: string;
  active_profile_name: string | null;
  active_profile_path: string | null;
  profile_exists: boolean;
  cookies_available: boolean;
  locked: boolean;
  detected_system_profiles: number;
  detected_managed_profiles: number;
  reuse_existing_session: boolean;
  clone_system_profile_on_lock: boolean;
}

export interface JobSummary {
  id: number;
  title: string;
  company: string;
  location: string | null;
  ats_source: string;
  status: string;
  source_url: string;
  created_at: ISODateTime;
  latest_score: number | null;
  resume_versions: number;
  applications_count: number;
}

export interface JobDetail extends JobSummary {
  description_text: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
}

export interface JobWorkspace {
  job: JobDetail;
  latest_score: {
    fit_score: number;
    salary_fit: number;
    skill_overlap: number;
    seniority_alignment: number;
    location_compatibility: number;
    confidence: number;
    composite: number;
    rationale: string;
    matched_skills: string[];
    missing_skills: string[];
    model_used: string;
    created_at: ISODateTime;
  } | null;
  resume_versions: Array<{
    id: number;
    template: string;
    kind: string;
    docx_path: string | null;
    pdf_path: string | null;
    created_at: ISODateTime;
  }>;
  applications: Array<{
    id: number;
    status: string;
    mode: string;
    source: string | null;
    cover_letter?: string | null;
    submitted_at: ISODateTime | null;
    created_at: ISODateTime;
  }>;
  recent_events: Array<{
    id: number;
    application_id: number;
    event_type: string;
    created_at: ISODateTime;
  }>;
  extracted_keywords: string[];
}

export interface ApplicationSummary {
  id: number;
  job_id: number;
  job_title: string | null;
  status: string;
  mode: string;
  submitted_at: ISODateTime | null;
  created_at: ISODateTime;
}

export interface ApplicationDetail extends ApplicationSummary {
  source: string | null;
  notes: string | null;
  recruiter_name: string | null;
  recruiter_email: string | null;
  cover_letter: string | null;
  confirmation_text: string | null;
  events: Array<{
    id: number;
    event_type: string;
    created_at: ISODateTime;
    payload: Record<string, unknown> | null;
  }>;
  generated_answers: Array<{
    id: number;
    question_text: string;
    generated_text: string;
    approved_text: string | null;
    category: string | null;
    approved: boolean;
    source: string;
    created_at: ISODateTime;
  }>;
}

export interface ResumeSummary {
  id: number;
  job_id: number | null;
  kind: string;
  template: string;
  docx_path: string | null;
  pdf_path: string | null;
  created_at: ISODateTime;
}

export interface ScoreView {
  job_id: number;
  fit_score: number;
  salary_fit: number;
  skill_overlap: number;
  seniority_alignment: number;
  location_compatibility: number;
  confidence: number;
  composite: number;
  rationale: string;
  matched_skills: string[];
  missing_skills: string[];
  model_used: string;
  created_at: ISODateTime;
}

export interface AutomationEventView {
  id: number;
  application_id: number;
  job_id: number | null;
  job_title: string | null;
  event_type: string;
  payload: Record<string, unknown> | null;
  created_at: ISODateTime;
}

export interface ScreenshotView {
  name: string;
  path: string;
  modified_at: ISODateTime;
  size_bytes: number;
}

export interface AutomationSessionView {
  application_id: number;
  job_id: number;
  job_title: string | null;
  status: string;
  mode: string;
  updated_at: ISODateTime;
  latest_event: string | null;
}

export interface AutomationOverview {
  active_sessions: number;
  pending_review: number;
  recent_sessions: AutomationSessionView[];
  recent_events: AutomationEventView[];
  recent_screenshots: ScreenshotView[];
}

export interface AIActivityEntry {
  timestamp: ISODateTime;
  level: string;
  logger: string;
  event: string;
  payload: Record<string, unknown>;
}

export interface AIActivitySummary {
  total_entries: number;
  validation_failures: number;
  avg_latency_ms: number | null;
}

export interface FunnelItem {
  stage: string;
  count: number;
}

export interface SourceEffectiveness {
  source: string;
  jobs: number;
  applications: number;
  submitted: number;
  submission_rate: number;
}

export interface ScoreBucket {
  label: string;
  min: number;
  max: number;
  count: number;
}

export interface TimelinePoint {
  day: string;
  jobs: number;
  applications: number;
  submitted: number;
}

export interface AnalyticsSummary {
  jobs_ingested_today: number;
  applications_pending_review: number;
  total_jobs: number;
  total_applications: number;
  funnel: FunnelItem[];
  score_distribution: ScoreBucket[];
  source_effectiveness: SourceEffectiveness[];
  timeline_14d: TimelinePoint[];
}

export interface SettingsBundle {
  profile: Record<string, unknown>;
  preferences: Record<string, unknown>;
  job_sources: Record<string, unknown>;
  blacklist: Record<string, unknown>;
  resume_master: Record<string, unknown>;
}

export type SettingsSection =
  | "profile"
  | "preferences"
  | "job_sources"
  | "blacklist"
  | "resume_master";

export type JobHuntStatusName = "idle" | "running" | "paused" | "stopped" | "error";

export type JobHuntMode =
  | "manual_review"
  | "assisted_apply"
  | "autonomous_apply"
  | "linkedin_assist";

export type RemotePreference = "remote" | "hybrid" | "onsite" | "no_preference";

export interface JobDiscoveryConfig {
  urls: string[];
  keywords: string[];
  companies: string[];
  locations: string[];
  remote_preference: RemotePreference;
  limit_per_source: number;
  run_search: boolean;
}

export interface JobHuntRunRequest {
  mode: JobHuntMode;
  run_once: boolean;
  interval_minutes: number | null;
  discovery: JobDiscoveryConfig;
}

export interface JobHuntStartRequest extends JobHuntRunRequest {
  save_defaults?: boolean;
}

export type PipelineStage =
  | "idle"
  | "discovering"
  | "ingesting"
  | "filtering"
  | "scoring"
  | "tailoring"
  | "preparing"
  | "awaiting_approval"
  | "submitting"
  | "cooldown"
  | "sleeping";

export interface OrchestratorQueueItem {
  url: string | null;
  job_id: number | null;
  title: string | null;
  company: string | null;
  stage: PipelineStage;
}

export interface JobHuntStats {
  jobs_seen: number;
  jobs_ingested: number;
  jobs_filtered: number;
  jobs_analyzed: number;
  resumes_generated: number;
  applications_attempted: number;
  applications_prepared?: number;
  applications_submitted: number;
  applications_skipped: number;
  errors: number;
}

export interface JobHuntStatus {
  status: JobHuntStatusName;
  stage?: PipelineStage;
  mode: JobHuntMode | null;
  run_once: boolean;
  interval_minutes: number | null;
  started_at: ISODateTime | null;
  last_tick_at: ISODateTime | null;
  stopped_at: ISODateTime | null;
  last_event: string | null;
  last_error: string | null;
  current_task: string | null;
  current_job_id?: number | null;
  current_job_title?: string | null;
  current_company?: string | null;
  queue?: OrchestratorQueueItem[];
  stats: JobHuntStats;
}

export interface IngestResult {
  url: string;
  status: "ingested" | "filtered" | "error";
  job_id: number | null;
  title: string | null;
  company: string | null;
  ats_source: string | null;
  error: string | null;
}

export interface BatchIngestResponse {
  total: number;
  ingested: number;
  failed: number;
  results: IngestResult[];
}

export interface SourceSummary {
  source: string;
  urls: number;
  ingested: number;
  failed: number;
}

export interface SearchResponse {
  sources: SourceSummary[];
  results: IngestResult[];
}

export interface ActivityEntry {
  timestamp: ISODateTime;
  category: string;
  title: string;
  detail: string | null;
  job_id: number | null;
  application_id: number | null;
  payload: Record<string, unknown> | null;
}

export type AutomationState = "idle" | "running" | "paused" | "stopped" | "manual_control";

export interface BrowserActionLog {
  action: string;
  detail: string | null;
  url: string | null;
  timestamp: string;
}

export interface RuntimeSnapshot {
  state: AutomationState;
  pause_all: boolean;
  current_url: string | null;
  current_title: string | null;
  current_task: string | null;
  current_form_step: string | null;
  session_id: string | null;
  application_id: number | null;
  last_screenshot: string | null;
  last_error: string | null;
  ai_summary: string | null;
  queued_actions: Array<{ id: string; action: string; detail: string | null; created_at: string }>;
  recent_actions: BrowserActionLog[];
  pending_approval_count: number;
}

export interface DiscoverySchedulerStatus {
  status: "idle" | "running" | "paused" | "stopped";
  interval_minutes: number;
  last_run_at: string | null;
  sources: Array<{
    name: string;
    enabled: boolean;
    last_poll_at: string | null;
    jobs_discovered: number;
    ingestion_failures: number;
    auth_status: string;
    rate_limit_until: string | null;
    health_status: string;
    last_error: string | null;
  }>;
  total_urls_found: number;
  total_ingested: number;
}

export interface SourceHealthView {
  name: string;
  type: string;
  enabled: boolean;
  health_status: string;
  message: string;
  authenticated: boolean | null;
  rate_limit_until: string | null;
}

export interface ApprovalQueueItem {
  id: number;
  application_id: number;
  job_id: number;
  company: string;
  role: string;
  checkpoint_type: string;
  status: string;
  confidence: number | null;
  resume_version_id: number | null;
  ai_summary: string | null;
  risks: string[];
  generated_answers: Record<string, unknown> | null;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export interface BlacklistSuggestionView {
  id: number;
  company: string;
  job_title: string;
  reason: string;
  status: string;
  matched_pattern: string | null;
  created_at: string;
}
