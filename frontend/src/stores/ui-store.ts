"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface UiState {
  sidebarCollapsed: boolean;
  commandOpen: boolean;
  jobsInspectorOpen: boolean;
  selectedJobId: number | null;
  toggleSidebar: () => void;
  setCommandOpen: (open: boolean) => void;
  setJobsInspectorOpen: (open: boolean) => void;
  setSelectedJobId: (jobId: number | null) => void;
}

export const useUiStore = create<UiState>()(
  persist(
    (set) => ({
      sidebarCollapsed: false,
      commandOpen: false,
      jobsInspectorOpen: true,
      selectedJobId: null,
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      setCommandOpen: (open) => set({ commandOpen: open }),
      setJobsInspectorOpen: (open) => set({ jobsInspectorOpen: open }),
      setSelectedJobId: (jobId) => set({ selectedJobId: jobId }),
    }),
    {
      name: "ops-console-ui",
      partialize: (state) => ({
        sidebarCollapsed: state.sidebarCollapsed,
        jobsInspectorOpen: state.jobsInspectorOpen,
      }),
    }
  )
);
