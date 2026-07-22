'use client';

import { create } from 'zustand';

import { api } from '@/lib/services/http';
import type { NormalizedBBox } from '@/lib/pdf/coords';

export interface ObservationReplyRow {
  public_id: string;
  author_email: string;
  body: string;
  status_change: string;
  created_at: string;
}

export interface ObservationAnchorRow {
  version_number: number;
  page: number;
  quads: NormalizedBBox[];
  text_snippet: string;
  method: 'exact' | 'reanchored_section' | 'orphaned';
}

export interface ObservationRow {
  public_id: string;
  body: string;
  status: 'open' | 'answered' | 'resolved';
  author_email: string;
  section_key: string | null;
  section_heading: string | null;
  created_on: number;
  resolved_in: number | null;
  replies: ObservationReplyRow[];
  anchors: ObservationAnchorRow[];
  created_at: string;
}

interface ObservationState {
  items: ObservationRow[];
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  fetch: (versionId: string) => Promise<void>;
  create: (
    versionId: string,
    payload: { body: string; sectionKey?: string }
  ) => Promise<boolean>;
  reply: (versionId: string, observationId: string, body: string) => Promise<boolean>;
  setStatus: (versionId: string, observationId: string, status: string) => Promise<boolean>;
}

function messageOf(err: unknown): string {
  return (
    (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
    (err as Error)?.message ??
    'Algo salió mal'
  );
}

export const useObservationStore = create<ObservationState>((set, get) => ({
  items: [],
  isLoading: false,
  isSubmitting: false,
  error: null,

  fetch: async (versionId) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get(`versions/${versionId}/observations/`);
      set({ items: data.results, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: messageOf(err) });
    }
  },

  create: async (versionId, { body, sectionKey }) => {
    set({ isSubmitting: true, error: null });
    try {
      await api.post(`versions/${versionId}/observations/`, {
        body,
        section_key: sectionKey ?? '',
      });
      set({ isSubmitting: false });
      await get().fetch(versionId);
      return true;
    } catch (err) {
      set({ isSubmitting: false, error: messageOf(err) });
      return false;
    }
  },

  reply: async (versionId, observationId, body) => {
    try {
      await api.post(`observations/${observationId}/replies/`, { body });
      await get().fetch(versionId);
      return true;
    } catch (err) {
      set({ error: messageOf(err) });
      return false;
    }
  },

  setStatus: async (versionId, observationId, status) => {
    try {
      await api.post(`observations/${observationId}/status/`, { status });
      await get().fetch(versionId);
      return true;
    } catch (err) {
      set({ error: messageOf(err) });
      return false;
    }
  },
}));
