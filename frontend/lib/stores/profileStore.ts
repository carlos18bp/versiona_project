'use client';

import { create } from 'zustand';

import { api } from '@/lib/services/http';
import { useLocaleStore } from '@/lib/stores/localeStore';
import type { Profile } from '@/lib/types';

interface ProfileState {
  profile: Profile | null;
  isLoading: boolean;
  isSaving: boolean;
  error: string | null;
  fetchProfile: () => Promise<void>;
  updateProfile: (patch: Partial<Profile>) => Promise<boolean>;
}

export const useProfileStore = create<ProfileState>((set) => ({
  profile: null,
  isLoading: false,
  isSaving: false,
  error: null,

  fetchProfile: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get<Profile>('me/profile/');
      set({ profile: data, isLoading: false });
      useLocaleStore.getState().setLocale(data.language);
    } catch (err) {
      set({ isLoading: false, error: (err as Error)?.message ?? 'Error' });
    }
  },

  updateProfile: async (patch) => {
    set({ isSaving: true, error: null });
    try {
      const { data } = await api.patch<Profile>('me/profile/', patch);
      set({ profile: data, isSaving: false });
      useLocaleStore.getState().setLocale(data.language);
      return true;
    } catch (err) {
      const message =
        (err as { response?: { data?: { timezone?: string[] } } })?.response?.data?.timezone?.[0] ??
        (err as Error)?.message ??
        'Error';
      set({ isSaving: false, error: message });
      return false;
    }
  },
}));
