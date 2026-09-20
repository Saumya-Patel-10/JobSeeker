"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/services/api/endpoints";
import { queryKeys } from "@/services/api/query-keys";
import type { SettingsSection } from "@/types/api";

export function useStatus() {
  return useQuery({
    queryKey: queryKeys.status,
    queryFn: () => api.status(),
    refetchInterval: 15_000,
  });
}

export function useJobs(params?: { limit?: number; offset?: number; status?: string }) {
  return useQuery({
    queryKey: queryKeys.jobs(params),
    queryFn: () => api.jobs(params),
  });
}

export function useJobDetail(jobId: number) {
  return useQuery({
    queryKey: queryKeys.jobDetail(jobId),
    queryFn: () => api.jobDetail(jobId),
    enabled: Number.isFinite(jobId),
  });
}

export function useJobWorkspace(jobId: number) {
  return useQuery({
    queryKey: queryKeys.jobWorkspace(jobId),
    queryFn: () => api.jobWorkspace(jobId),
    enabled: Number.isFinite(jobId),
  });
}

export function useApplications(params?: {
  status?: string;
  limit?: number;
  offset?: number;
}) {
  return useQuery({
    queryKey: queryKeys.applications(params),
    queryFn: () => api.applications(params),
    refetchInterval: 10_000,
  });
}

export function useApplicationDetail(applicationId: number) {
  return useQuery({
    queryKey: queryKeys.applicationDetail(applicationId),
    queryFn: () => api.applicationDetail(applicationId),
    enabled: Number.isFinite(applicationId),
    refetchInterval: 10_000,
  });
}

export function useResumesForJob(jobId: number) {
  return useQuery({
    queryKey: queryKeys.resumesForJob(jobId),
    queryFn: () => api.resumesForJob(jobId),
    enabled: Number.isFinite(jobId),
  });
}

export function useScore(jobId: number) {
  return useQuery({
    queryKey: queryKeys.score(jobId),
    queryFn: () => api.score(jobId),
    enabled: Number.isFinite(jobId),
  });
}

export function useProfile() {
  return useQuery({
    queryKey: queryKeys.profile,
    queryFn: () => api.profile(),
  });
}

export function useSettings() {
  return useQuery({
    queryKey: queryKeys.settings,
    queryFn: () => api.settings(),
  });
}

export function useAnalyticsSummary() {
  return useQuery({
    queryKey: queryKeys.analyticsSummary,
    queryFn: () => api.analyticsSummary(),
    refetchInterval: 20_000,
  });
}

export function useAutomationOverview() {
  return useQuery({
    queryKey: queryKeys.automationOverview,
    queryFn: () => api.automationOverview(),
    refetchInterval: 8_000,
  });
}

export function useAutomationSessions(limit = 50) {
  return useQuery({
    queryKey: queryKeys.automationSessions(limit),
    queryFn: () => api.automationSessions(limit),
    refetchInterval: 8_000,
  });
}

export function useAutomationEvents(params?: { application_id?: number; limit?: number }) {
  return useQuery({
    queryKey: queryKeys.automationEvents(params),
    queryFn: () => api.automationEvents(params),
    refetchInterval: 6_000,
  });
}

export function useAIActivity(limit = 200) {
  return useQuery({
    queryKey: queryKeys.aiActivity(limit),
    queryFn: () => api.aiActivity(limit),
    refetchInterval: 6_000,
  });
}

export function useAISummary(limit = 500) {
  return useQuery({
    queryKey: queryKeys.aiSummary(limit),
    queryFn: () => api.aiSummary(limit),
    refetchInterval: 10_000,
  });
}

export function useBrowserProfiles() {
  return useQuery({
    queryKey: queryKeys.browserProfiles,
    queryFn: () => api.browserProfiles(),
    refetchInterval: 8_000,
  });
}

export function useBrowserHealth() {
  return useQuery({
    queryKey: queryKeys.browserHealth,
    queryFn: () => api.browserHealth(),
    refetchInterval: 8_000,
  });
}

export function useJobHuntStatus() {
  return useQuery({
    queryKey: queryKeys.jobHuntStatus,
    queryFn: () => api.jobHuntStatus(),
    refetchInterval: 5_000,
  });
}

export function useControlCenterActivity(limit = 120) {
  return useQuery({
    queryKey: queryKeys.controlCenterActivity(limit),
    queryFn: () => api.controlCenterActivity(limit),
    refetchInterval: 5_000,
  });
}

export function useStartJobHunt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.startJobHunt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobHuntStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
      queryClient.invalidateQueries({ queryKey: queryKeys.automationOverview });
    },
  });
}

export function usePauseJobHunt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.pauseJobHunt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobHuntStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
    },
  });
}

export function useResumeJobHunt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.resumeJobHunt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobHuntStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
    },
  });
}

export function useStopJobHunt() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.stopJobHunt,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobHuntStatus });
      queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
    },
  });
}

export function useIngestUrls() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.ingestUrls,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs() });
      queryClient.invalidateQueries({ queryKey: queryKeys.analyticsSummary });
      queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
    },
  });
}

export function useSearchSources() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: api.searchSources,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.jobs() });
      queryClient.invalidateQueries({ queryKey: queryKeys.analyticsSummary });
      queryClient.invalidateQueries({ queryKey: queryKeys.controlCenterActivity(120) });
    },
  });
}

export function useUpdateApplicationStatus() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      applicationId: number;
      status: string;
      notes?: string | null;
      confirmation_text?: string | null;
    }) =>
      api.updateApplicationStatus(payload.applicationId, {
        status: payload.status,
        notes: payload.notes,
        confirmation_text: payload.confirmation_text,
      }),
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: ["applications"] });
      const snapshots = queryClient.getQueriesData({
        queryKey: ["applications"],
      });
      for (const [key, value] of snapshots) {
        if (!Array.isArray(value)) {
          continue;
        }
        queryClient.setQueryData(
          key,
          value.map((item) =>
            item && typeof item === "object" && "id" in item && item.id === payload.applicationId
              ? { ...item, status: payload.status }
              : item
          )
        );
      }
      return { snapshots };
    },
    onError: (_error, _payload, context) => {
      if (!context?.snapshots) {
        return;
      }
      for (const [key, value] of context.snapshots) {
        queryClient.setQueryData(key, value);
      }
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.applications() });
      queryClient.invalidateQueries({ queryKey: queryKeys.applicationDetail(data.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.automationOverview });
      queryClient.invalidateQueries({ queryKey: queryKeys.analyticsSummary });
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profile: Record<string, unknown>) => api.updateProfile(profile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
    },
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      section: SettingsSection;
      data: Record<string, unknown>;
    }) => api.updateSettings(payload.section, payload.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
      queryClient.invalidateQueries({ queryKey: queryKeys.status });
      queryClient.invalidateQueries({ queryKey: queryKeys.profile });
    },
  });
}

export function useCloneBrowserProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      source_profile_name: string;
      target_name?: string;
      overwrite?: boolean;
    }) => api.cloneBrowserProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.browserProfiles });
      queryClient.invalidateQueries({ queryKey: queryKeys.browserHealth });
      queryClient.invalidateQueries({ queryKey: queryKeys.status });
    },
  });
}

export function useSetActiveBrowserProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: {
      profile_source: "system" | "managed";
      profile_name: string;
      persistent_profile?: boolean;
      reuse_existing_session?: boolean;
      clone_system_profile_on_lock?: boolean;
    }) => api.setActiveBrowserProfile(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.browserProfiles });
      queryClient.invalidateQueries({ queryKey: queryKeys.browserHealth });
      queryClient.invalidateQueries({ queryKey: queryKeys.status });
      queryClient.invalidateQueries({ queryKey: queryKeys.settings });
    },
  });
}

export function useRuntimeSnapshot() {
  return useQuery({
    queryKey: queryKeys.runtime,
    queryFn: () => api.runtimeSnapshot(),
    refetchInterval: 5_000,
  });
}

export function useDiscoveryStatus() {
  return useQuery({
    queryKey: queryKeys.discoveryStatus,
    queryFn: () => api.discoveryStatus(),
    refetchInterval: 8_000,
  });
}

export function useSourceHealth() {
  return useQuery({
    queryKey: queryKeys.sourceHealth,
    queryFn: () => api.sourceHealth(),
    refetchInterval: 30_000,
  });
}

export function usePendingApprovals() {
  return useQuery({
    queryKey: queryKeys.approvals,
    queryFn: () => api.pendingApprovals(),
    refetchInterval: 5_000,
  });
}

export function useBlacklistSuggestions() {
  return useQuery({
    queryKey: queryKeys.blacklistSuggestions,
    queryFn: () => api.blacklistSuggestions(),
    refetchInterval: 10_000,
  });
}

export function useApproveBlacklistSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.approveBlacklistSuggestion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.blacklistSuggestions });
    },
  });
}

export function useRejectBlacklistSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.rejectBlacklistSuggestion(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.blacklistSuggestions });
    },
  });
}

export function useApproveCheckpoint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, submit }: { id: number; submit?: boolean }) =>
      api.approveCheckpoint(id, submit),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.approvals });
      queryClient.invalidateQueries({ queryKey: queryKeys.applications() });
    },
  });
}

export function useRejectCheckpoint() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.rejectCheckpoint(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.approvals });
    },
  });
}

export function useAutomationControl() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.runtime });
    queryClient.invalidateQueries({ queryKey: queryKeys.discoveryStatus });
  };
  return {
    pause: useMutation({ mutationFn: () => api.pauseAutomation(), onSuccess: invalidate }),
    resume: useMutation({ mutationFn: () => api.resumeAutomation(), onSuccess: invalidate }),
    stop: useMutation({ mutationFn: () => api.stopAutomation(), onSuccess: invalidate }),
    pauseAll: useMutation({ mutationFn: () => api.pauseAllAutomation(), onSuccess: invalidate }),
    manual: useMutation({ mutationFn: () => api.manualControl(), onSuccess: invalidate }),
    returnAi: useMutation({ mutationFn: () => api.returnToAi(), onSuccess: invalidate }),
    startDiscovery: useMutation({
      mutationFn: api.startDiscovery,
      onSuccess: invalidate,
    }),
    pauseDiscovery: useMutation({
      mutationFn: () => api.pauseDiscovery(),
      onSuccess: invalidate,
    }),
    stopDiscovery: useMutation({
      mutationFn: () => api.stopDiscovery(),
      onSuccess: invalidate,
    }),
  };
}
