"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  CirclePause,
  CirclePlay,
  CloudUpload,
  Play,
  RefreshCw,
  Search,
  Sparkles,
  Square,
} from "lucide-react";
import { toast } from "sonner";

import { TRACK_LIST } from "@/features/jobs/role-tracks";

import { PageHeader } from "@/components/layout/page-header";
import { MetricCard } from "@/components/primitives/metric-card";
import { StatusPill } from "@/components/workflow/status-pill";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  useAutomationOverview,
  useBrowserHealth,
  useBrowserProfiles,
  useCloneBrowserProfile,
  useControlCenterActivity,
  useIngestUrls,
  useJobHuntStatus,
  usePauseJobHunt,
  useResumeJobHunt,
  useSearchSources,
  useSetActiveBrowserProfile,
  useSettings,
  useStartJobHunt,
  useStatus,
  useStopJobHunt,
  useUpdateSettings,
  useAutomationControl,
  useDiscoveryStatus,
} from "@/hooks/use-console-queries";
import { useEventWebSocket } from "@/hooks/use-event-websocket";
import { ApprovalQueuePanel } from "@/features/control/approval-queue-panel";
import { BlacklistSuggestionsPanel } from "@/features/control/blacklist-suggestions-panel";
import { SourceHealthPanel } from "@/features/control/source-health-panel";
import type { JobDiscoveryConfig, JobHuntMode, RemotePreference } from "@/types/api";
import { formatDateTime } from "@/utils/format";

const modeOptions: Array<{ value: JobHuntMode; label: string; helper: string }> = [
  {
    value: "manual_review",
    label: "Manual review",
    helper: "Fill forms and stop for approval.",
  },
  {
    value: "assisted_apply",
    label: "Assisted apply",
    helper: "Score + tailor only. No auto-fill.",
  },
  {
    value: "autonomous_apply",
    label: "Autonomous apply",
    helper: "Auto-fill + auto-submit (requires safety toggle).",
  },
  {
    value: "linkedin_assist",
    label: "LinkedIn assist-only",
    helper: "Never auto-submit LinkedIn. Always stop for review.",
  },
];

function parseList(value: string) {
  return value
    .split(/[\n,]+/)
    .map((entry) => entry.trim())
    .filter(Boolean);
}

function parseUrls(value: string) {
  return parseList(value).filter((entry) => entry.startsWith("http"));
}

export function ControlCenterPage() {
  const status = useStatus();
  const automation = useAutomationOverview();
  const browserHealth = useBrowserHealth();
  const browserProfiles = useBrowserProfiles();
  const jobHuntStatus = useJobHuntStatus();
  const { connected: wsConnected } = useEventWebSocket();
  const activity = useControlCenterActivity(120);
  const settings = useSettings();

  const startHunt = useStartJobHunt();
  const pauseHunt = usePauseJobHunt();
  const resumeHunt = useResumeJobHunt();
  const stopHunt = useStopJobHunt();
  const ingestUrls = useIngestUrls();
  const searchSources = useSearchSources();
  const updateSettings = useUpdateSettings();
  const cloneProfile = useCloneBrowserProfile();
  const setActiveProfile = useSetActiveBrowserProfile();

  const [mode, setMode] = useState<JobHuntMode>("manual_review");
  const [runOnce, setRunOnce] = useState(true);
  const [intervalMinutes, setIntervalMinutes] = useState(30);
  const [runSearch, setRunSearch] = useState(true);
  const [limitPerSource, setLimitPerSource] = useState(25);
  const [urlsText, setUrlsText] = useState("");
  const [keywordsText, setKeywordsText] = useState("");
  const [companiesText, setCompaniesText] = useState("");
  const [locationsText, setLocationsText] = useState("");
  const [remotePreference, setRemotePreference] = useState<RemotePreference>(
    "no_preference"
  );
  const [saveDefaults, setSaveDefaults] = useState(false);

  const [maxPerDay, setMaxPerDay] = useState(20);
  const [maxConcurrent, setMaxConcurrent] = useState(1);
  const [cooldownSeconds, setCooldownSeconds] = useState(90);
  const [headless, setHeadless] = useState(false);
  const [allowAutoSubmit, setAllowAutoSubmit] = useState(false);

  const [profileChoice, setProfileChoice] = useState<string>("");
  const [cloneTarget, setCloneTarget] = useState("");

  const initialized = useRef(false);

  useEffect(() => {
    if (!settings.data?.preferences || initialized.current) {
      return;
    }
    const prefs = settings.data.preferences as Record<string, any>;
    setKeywordsText((prefs.role_keywords ?? []).join(", "));
    setCompaniesText((prefs.target_companies ?? []).join(", "));
    setLocationsText((prefs.locations ?? []).join(", "));
    setRemotePreference((prefs.remote_preference ?? "no_preference") as RemotePreference);
    setIntervalMinutes(prefs.automation?.default_interval_minutes ?? 30);
    setMaxPerDay(prefs.apply?.daily_limit ?? 20);
    setMaxConcurrent(prefs.automation?.max_concurrent_sessions ?? 1);
    setCooldownSeconds(prefs.automation?.cooldown_seconds ?? 90);
    setHeadless(prefs.browser?.headless ?? false);
    setAllowAutoSubmit(prefs.apply?.allow_auto_submit ?? false);
    initialized.current = true;
  }, [settings.data]);

  const statusName = jobHuntStatus.data?.status ?? "idle";
  const pipelineStage = jobHuntStatus.data?.stage ?? "idle";
  const isRunning = statusName === "running";
  const isPaused = statusName === "paused";
  const canStart = statusName === "idle" || statusName === "stopped" || statusName === "error";
  const huntStats = jobHuntStatus.data?.stats;
  const jobQueue = jobHuntStatus.data?.queue ?? [];

  const discoveryPayload: JobDiscoveryConfig = {
    urls: parseUrls(urlsText),
    keywords: parseList(keywordsText),
    companies: parseList(companiesText),
    locations: parseList(locationsText),
    remote_preference: remotePreference,
    limit_per_source: limitPerSource,
    run_search: runSearch,
  };

  const profileOptions = useMemo(() => {
    const rows = browserProfiles.data ?? [];
    return rows.map((profile) => ({
      key: `${profile.source}:${profile.name}`,
      label: `${profile.name} (${profile.source})`,
      profile,
    }));
  }, [browserProfiles.data]);

  const selectedProfile = profileOptions.find((option) => option.key === profileChoice)?.profile;

  useEffect(() => {
    if (profileChoice || !browserHealth.data) {
      return;
    }
    const activeKey = `${browserHealth.data.profile_source}:${browserHealth.data.active_profile_name ?? ""}`;
    const match = profileOptions.find((option) => option.key === activeKey);
    if (match) {
      setProfileChoice(match.key);
    } else if (profileOptions.length) {
      setProfileChoice(profileOptions[0].key);
    }
  }, [browserHealth.data, profileChoice, profileOptions]);

  async function handleStart() {
    if (!discoveryPayload.run_search && !discoveryPayload.urls.length) {
      toast.error("Add URLs or enable search sources before starting.");
      return;
    }
    await startHunt.mutateAsync({
      mode,
      run_once: runOnce,
      interval_minutes: runOnce ? null : intervalMinutes,
      discovery: discoveryPayload,
      save_defaults: saveDefaults,
    });
    toast.success("Job hunt started");
  }

  async function handlePauseResume() {
    if (isPaused) {
      await resumeHunt.mutateAsync();
      toast.success("Job hunt resumed");
      return;
    }
    if (isRunning) {
      await pauseHunt.mutateAsync();
      toast.success("Job hunt paused");
    }
  }

  async function handleStop() {
    await stopHunt.mutateAsync();
    toast.success("Job hunt stopped");
  }

  async function handleIngest() {
    if (!discoveryPayload.urls.length) {
      toast.error("Paste one or more URLs to ingest.");
      return;
    }
    await ingestUrls.mutateAsync({ urls: discoveryPayload.urls });
    toast.success("Ingest request submitted");
  }

  async function handleSearch() {
    await searchSources.mutateAsync({
      limit: limitPerSource,
      discovery: discoveryPayload,
      save_defaults: saveDefaults,
    });
    toast.success("Search started");
  }

  async function handleSaveAutomation() {
    const prefs = (settings.data?.preferences ?? {}) as Record<string, any>;
    const next = {
      ...prefs,
      apply: {
        ...(prefs.apply ?? {}),
        daily_limit: maxPerDay,
        allow_auto_submit: allowAutoSubmit,
      },
      automation: {
        ...(prefs.automation ?? {}),
        max_concurrent_sessions: maxConcurrent,
        cooldown_seconds: cooldownSeconds,
        default_interval_minutes: intervalMinutes,
      },
      browser: {
        ...(prefs.browser ?? {}),
        headless,
      },
    };
    await updateSettings.mutateAsync({ section: "preferences", data: next });
    toast.success("Automation settings saved");
  }

  async function handleProfileActivate() {
    if (!selectedProfile) {
      toast.error("Select a Firefox profile first.");
      return;
    }
    await setActiveProfile.mutateAsync({
      profile_source: selectedProfile.source,
      profile_name: selectedProfile.name,
      persistent_profile: true,
      reuse_existing_session: true,
      clone_system_profile_on_lock: true,
    });
    toast.success(`Activated ${selectedProfile.name}`);
  }

  async function handleProfileClone() {
    if (!selectedProfile || selectedProfile.source !== "system") {
      toast.error("Choose a system Firefox profile to clone.");
      return;
    }
    const target = cloneTarget.trim() || `${selectedProfile.name}-managed`;
    await cloneProfile.mutateAsync({
      source_profile_name: selectedProfile.name,
      target_name: target,
      overwrite: false,
    });
    toast.success(`Cloned to ${target}`);
  }

  async function handleUpload(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const text = await file.text();
    setUrlsText((prev) => `${prev}\n${text}`.trim());
  }

  return (
    <div className="space-y-4">
      <PageHeader
        title="Control Center"
        description="Single supervised pipeline: discover → score → tailor → prepare → approve → submit."
        right={
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={wsConnected ? "secondary" : "outline"} className="text-xs">
              {wsConnected ? "live" : "polling"}
            </Badge>
            <Button
              onClick={handleStart}
              disabled={!canStart || startHunt.isPending}
              className="gap-2"
            >
              <Play className="size-4" />
              Start Job Hunt
            </Button>
            <Button
              variant="outline"
              onClick={handlePauseResume}
              disabled={!isRunning && !isPaused}
              className="gap-2"
            >
              {isPaused ? <CirclePlay className="size-4" /> : <CirclePause className="size-4" />}
              {isPaused ? "Resume" : "Pause"}
            </Button>
            <Button
              variant="outline"
              onClick={handleStop}
              disabled={!isRunning && !isPaused}
              className="gap-2"
            >
              <Square className="size-4" />
              Stop
            </Button>
          </div>
        }
      />

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="panel xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Core Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap items-center gap-3">
              <StatusPill status={statusName} />
              <Badge variant="outline" className="font-mono text-xs">
                stage: {pipelineStage}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {jobHuntStatus.data?.current_job_title
                  ? `${jobHuntStatus.data.current_job_title} @ ${jobHuntStatus.data.current_company ?? "?"}`
                  : jobHuntStatus.data?.current_task ?? "no active job"}
              </span>
            </div>
            {huntStats ? (
              <div className="grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                <div>seen: {huntStats.jobs_seen}</div>
                <div>ingested: {huntStats.jobs_ingested}</div>
                <div>scored: {huntStats.jobs_analyzed}</div>
                <div>prepared: {huntStats.applications_prepared ?? huntStats.applications_attempted}</div>
              </div>
            ) : null}
            {jobQueue.length > 0 ? (
              <div className="rounded-xl border border-border/70 p-2">
                <p className="text-xs font-medium text-muted-foreground mb-1">Job queue (next {Math.min(jobQueue.length, 8)})</p>
                <ul className="max-h-24 overflow-auto text-xs space-y-1">
                  {jobQueue.slice(0, 8).map((item, idx) => (
                    <li key={`${item.url ?? item.job_id}-${idx}`} className="truncate text-muted-foreground">
                      {item.title ?? item.url ?? `job #${item.job_id}`}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
            <p className="text-xs text-muted-foreground">
              {jobHuntStatus.data?.started_at
                ? `started ${formatDateTime(jobHuntStatus.data.started_at)}`
                : ""}
              {jobHuntStatus.data?.last_tick_at
                ? ` · last tick ${formatDateTime(jobHuntStatus.data.last_tick_at)}`
                : ""}
            </p>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Job Search Mode</p>
                <div className="grid gap-2">
                  {modeOptions.map((option) => (
                    <button
                      key={option.value}
                      type="button"
                      onClick={() => setMode(option.value)}
                      className={`rounded-xl border px-3 py-2 text-left text-sm transition ${
                        mode === option.value
                          ? "border-primary/60 bg-primary/10"
                          : "border-border/70 hover:border-primary/40"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{option.label}</span>
                        {mode === option.value ? <Badge variant="secondary">selected</Badge> : null}
                      </div>
                      <p className="text-xs text-muted-foreground">{option.helper}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Run Schedule</p>
                <div className="rounded-xl border border-border/70 p-3 space-y-3">
                  <label className="flex items-center justify-between text-sm">
                    Run once per click
                    <Switch checked={runOnce} onCheckedChange={setRunOnce} />
                  </label>
                  {!runOnce ? (
                    <div className="space-y-1">
                      <label className="text-xs text-muted-foreground">Interval minutes</label>
                      <Input
                        type="number"
                        min={1}
                        value={intervalMinutes}
                        onChange={(event) => setIntervalMinutes(Number(event.target.value || 0))}
                      />
                    </div>
                  ) : null}
                  <label className="flex items-center justify-between text-sm">
                    Use configured sources
                    <Switch checked={runSearch} onCheckedChange={setRunSearch} />
                  </label>
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Max results per source</label>
                    <Input
                      type="number"
                      min={1}
                      max={250}
                      value={limitPerSource}
                      onChange={(event) => setLimitPerSource(Number(event.target.value || 0))}
                    />
                  </div>
                </div>
              </div>
            </div>

            {jobHuntStatus.data?.last_error ? (
              <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-3 text-xs text-destructive">
                {jobHuntStatus.data.last_error}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Runtime Status</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>Backend</span>
                <StatusPill status={status.data?.healthy ? "running" : "error"} />
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>LLM</span>
                <StatusPill status={status.data?.llm_reachable ? "running" : "error"} />
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Firefox session</span>
                <StatusPill
                  status={browserHealth.data?.cookies_available ? "running" : "paused"}
                />
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Automation queue</span>
                <span className="text-sm font-medium">
                  {automation.data?.pending_review ?? 0} pending
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span>Active sessions</span>
                <span className="text-sm font-medium">
                  {automation.data?.active_sessions ?? 0}
                </span>
              </div>
              <div className="text-xs text-muted-foreground">
                last event: {automation.data?.recent_events?.[0]?.event_type ?? "n/a"}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="panel xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Job Discovery</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid gap-3 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground">Paste job URLs</label>
                <Textarea
                  value={urlsText}
                  onChange={(event) => setUrlsText(event.target.value)}
                  placeholder="One URL per line"
                  className="min-h-[140px]"
                />
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <Input type="file" accept=".txt" onChange={handleUpload} />
                  <span>Upload a text file with URLs.</span>
                </div>
              </div>

              <div className="space-y-2">
                <div className="rounded-xl border border-indigo-500/20 bg-indigo-500/5 p-3 space-y-2 mb-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <Sparkles className="size-3.5 text-indigo-500" />
                      Role Track Presets:
                    </span>
                    <span className="text-[11px] text-muted-foreground">Click to set keywords</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {TRACK_LIST.map((track) => (
                      <Button
                        key={track.id}
                        type="button"
                        variant="outline"
                        size="sm"
                        className="h-7 gap-1 rounded-lg border-border/80 bg-card text-xs font-medium hover:border-primary/50"
                        onClick={() => {
                          setKeywordsText(track.keywords.join(", "));
                          toast.success(`Loaded keywords for ${track.label}`);
                        }}
                      >
                        <span>{track.badge}</span>
                      </Button>
                    ))}
                  </div>
                </div>

                <label className="text-xs text-muted-foreground">Search filters</label>
                <Input
                  value={keywordsText}
                  onChange={(event) => setKeywordsText(event.target.value)}
                  placeholder="Keywords (comma-separated)"
                />
                <Input
                  value={companiesText}
                  onChange={(event) => setCompaniesText(event.target.value)}
                  placeholder="Target companies"
                />
                <Input
                  value={locationsText}
                  onChange={(event) => setLocationsText(event.target.value)}
                  placeholder="Locations (comma-separated)"
                />
                <div className="space-y-1">
                  <label className="text-xs text-muted-foreground">Remote preference</label>
                  <Select value={remotePreference} onValueChange={(value) => setRemotePreference(value as RemotePreference)}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Select preference" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="no_preference">No preference</SelectItem>
                      <SelectItem value="remote">Remote</SelectItem>
                      <SelectItem value="hybrid">Hybrid</SelectItem>
                      <SelectItem value="onsite">Onsite</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <label className="flex items-center justify-between text-sm">
                  Save as default
                  <Switch checked={saveDefaults} onCheckedChange={setSaveDefaults} />
                </label>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button onClick={handleIngest} disabled={ingestUrls.isPending} className="gap-2">
                <CloudUpload className="size-4" />
                Ingest Jobs
              </Button>
              <Button
                variant="outline"
                onClick={handleSearch}
                disabled={searchSources.isPending}
                className="gap-2"
              >
                <Search className="size-4" />
                Discover & ingest
              </Button>
              <Button
                variant="ghost"
                onClick={() => {
                  ingestUrls.reset();
                  searchSources.reset();
                }}
                className="gap-2"
              >
                <RefreshCw className="size-4" />
                Clear results
              </Button>
            </div>

            {ingestUrls.data || searchSources.data ? (
              <div className="rounded-xl border border-border/70 p-3 text-sm">
                <p className="font-medium">Latest ingestion summary</p>
                <p className="text-xs text-muted-foreground">
                  {ingestUrls.data
                    ? `${ingestUrls.data.ingested}/${ingestUrls.data.total} ingested (${ingestUrls.data.failed} failed)`
                    : searchSources.data
                    ? searchSources.data.sources
                        .map(
                          (s) =>
                            `${s.source}: ${s.ingested}/${s.urls} ingested (${s.failed} failed)`
                        )
                        .join(" · ")
                    : ""}
                </p>
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Automation Controls</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Max applications per day</label>
              <Input
                type="number"
                min={1}
                value={maxPerDay}
                onChange={(event) => setMaxPerDay(Number(event.target.value || 0))}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Max concurrent sessions</label>
              <Input
                type="number"
                min={1}
                value={maxConcurrent}
                onChange={(event) => setMaxConcurrent(Number(event.target.value || 0))}
              />
              <p className="text-[11px] text-muted-foreground">Currently enforced sequentially.</p>
            </div>
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Cooldown between applications (seconds)</label>
              <Input
                type="number"
                min={0}
                value={cooldownSeconds}
                onChange={(event) => setCooldownSeconds(Number(event.target.value || 0))}
              />
            </div>
            <label className="flex items-center justify-between text-sm">
              Headless browser mode
              <Switch checked={headless} onCheckedChange={setHeadless} />
            </label>
            <label className="flex items-center justify-between text-sm">
              Allow auto-submit
              <Switch checked={allowAutoSubmit} onCheckedChange={setAllowAutoSubmit} />
            </label>
            <Button onClick={handleSaveAutomation} disabled={updateSettings.isPending}>
              Save automation settings
            </Button>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <Card className="panel xl:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm">Live Activity Feed</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[42vh]">
              <div className="space-y-2 pr-2">
                {activity.data?.map((entry) => (
                  <div key={`${entry.timestamp}-${entry.title}`} className="rounded-xl border border-border/70 p-3">
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-medium">{entry.title}</p>
                      <span className="text-xs text-muted-foreground">
                        {formatDateTime(entry.timestamp)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {entry.category} {entry.detail ? `· ${entry.detail}` : ""}
                    </p>
                    {entry.payload && Object.keys(entry.payload).length ? (
                      <pre className="mt-2 overflow-auto rounded-lg bg-muted/40 p-2 text-[11px]">
                        {JSON.stringify(entry.payload, null, 2)}
                      </pre>
                    ) : null}
                  </div>
                ))}
                {!activity.data?.length ? (
                  <div className="rounded-xl border border-dashed border-border p-4 text-sm text-muted-foreground">
                    No activity yet. Start a job hunt or ingest jobs to populate the feed.
                  </div>
                ) : null}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardHeader>
            <CardTitle className="text-sm">Firefox Integration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricCard
              label="Active Profile"
              value={browserHealth.data?.active_profile_name ?? "none"}
              hint={browserHealth.data?.profile_source ?? "managed"}
              icon={<Activity className="size-4" />}
            />
            <div className="space-y-2">
              <label className="text-xs text-muted-foreground">Select profile</label>
              <Select value={profileChoice} onValueChange={(val) => setProfileChoice(val ?? "")}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Choose a profile" />
                </SelectTrigger>
                <SelectContent>
                  {profileOptions.map((option) => (
                    <SelectItem key={option.key} value={option.key}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <div className="flex flex-wrap gap-2">
                <Button onClick={handleProfileActivate} disabled={setActiveProfile.isPending}>
                  Use profile
                </Button>
                <Button
                  variant="outline"
                  onClick={handleProfileClone}
                  disabled={cloneProfile.isPending || selectedProfile?.source !== "system"}
                >
                  Clone to managed
                </Button>
              </div>
              <Input
                placeholder="Clone target name"
                value={cloneTarget}
                onChange={(event) => setCloneTarget(event.target.value)}
              />
              <p className="text-xs text-muted-foreground">
                Cookies available: {browserHealth.data?.cookies_available ? "yes" : "no"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <SourceHealthPanel />
        <ApprovalQueuePanel />
        <BlacklistSuggestionsPanel />
      </section>
    </div>
  );
}
