'use client';

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

import { api } from '@/lib/services/http';
import type { OrgSummary } from '@/lib/types';

interface OrgState {
  orgs: OrgSummary[];
  activeOrgId: string | null;
  isLoading: boolean;
  error: string | null;
  fetchOrgs: () => Promise<void>;
  setActiveOrg: (publicId: string) => void;
  reset: () => void;
}

export const useOrgStore = create<OrgState>()(
  persist(
    (set, get) => ({
      orgs: [],
      activeOrgId: null,
      isLoading: false,
      error: null,

      fetchOrgs: async () => {
        set({ isLoading: true, error: null });
        try {
          const { data } = await api.get('orgs/');
          const orgs: OrgSummary[] = data.results ?? [];
          const active = get().activeOrgId;
          const stillValid = orgs.some((org) => org.public_id === active);
          set({
            orgs,
            isLoading: false,
            activeOrgId: stillValid ? active : orgs[0]?.public_id ?? null,
          });
        } catch (err) {
          set({
            isLoading: false,
            error: (err as Error)?.message ?? 'No se pudieron cargar las organizaciones',
          });
        }
      },

      setActiveOrg: (publicId) => set({ activeOrgId: publicId }),
      reset: () => set({ orgs: [], activeOrgId: null, error: null, isLoading: false }),
    }),
    { name: 'versiona-org', partialize: (state) => ({ activeOrgId: state.activeOrgId }) }
  )
);

export const selectActiveOrg = (state: OrgState) =>
  state.orgs.find((org) => org.public_id === state.activeOrgId) ?? null;
