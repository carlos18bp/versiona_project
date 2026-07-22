'use client';

import { create } from 'zustand';

import { api } from '@/lib/services/http';

export interface TrialInfo {
  on_trial: boolean;
  trial_ends_at: string | null;
  days_left: number | null;
}

interface TrialState {
  trial: TrialInfo | null;
  fetchedOrgId: string | null;
  fetch: (orgId: string) => Promise<void>;
}

// One usage fetch per active org per session — the banner only needs the
// trial block, and the usage page keeps its own richer fetch.
export const useTrialStore = create<TrialState>((set, get) => ({
  trial: null,
  fetchedOrgId: null,
  fetch: async (orgId) => {
    if (get().fetchedOrgId === orgId) return;
    set({ fetchedOrgId: orgId });
    try {
      const { data } = await api.get(`orgs/${orgId}/usage/`);
      set({ trial: data.trial ?? null });
    } catch {
      set({ trial: null });
    }
  },
}));
