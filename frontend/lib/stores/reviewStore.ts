'use client';

import { create } from 'zustand';

import { api } from '@/lib/services/http';

export interface ReviewAssignmentRow {
  reviewer_email: string;
  scope: string | string[];
  status: 'pending' | 'done';
  completed_at: string | null;
}

export interface ReviewRequestRow {
  public_id: string;
  status: 'open' | 'completed' | 'cancelled' | 'superseded';
  message: string;
  requested_by_email: string;
  version_number: number;
  assignments: ReviewAssignmentRow[];
  created_at: string;
  closed_at: string | null;
}

export interface InboxAssignment {
  review: string;
  document_title: string;
  version_number: number;
  project_name: string;
  requested_by: string;
  message: string;
  scope: string | string[];
  requested_at: string;
  link: string;
}

export interface ReviewContext {
  my_last_sealed_version: number | null;
  changed: Array<{ stable_key: string; heading: string }>;
  unchanged: Array<{ stable_key: string; heading: string }>;
}

export interface ProjectMember {
  id: number;
  email: string;
  first_name: string;
  role: 'admin' | 'editor' | 'reviewer' | 'viewer';
}

interface ReviewState {
  requests: ReviewRequestRow[];
  assignments: InboxAssignment[];
  context: ReviewContext | null;
  members: ProjectMember[];
  isLoading: boolean;
  isSubmitting: boolean;
  error: string | null;
  fetchRequests: (versionId: string) => Promise<void>;
  createRequest: (
    versionId: string,
    reviewerIds: number[],
    message: string
  ) => Promise<boolean>;
  cancelRequest: (versionId: string, reviewId: string) => Promise<boolean>;
  fetchAssignments: () => Promise<void>;
  fetchContext: (versionId: string) => Promise<void>;
  fetchMembers: (projectId: string) => Promise<void>;
}

function messageOf(err: unknown): string {
  return (
    (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
    (err as Error)?.message ??
    'Algo salió mal'
  );
}

export const useReviewStore = create<ReviewState>((set, get) => ({
  requests: [],
  assignments: [],
  context: null,
  members: [],
  isLoading: false,
  isSubmitting: false,
  error: null,

  fetchRequests: async (versionId) => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get(`versions/${versionId}/reviews/`);
      set({ requests: data.results, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: messageOf(err) });
    }
  },

  createRequest: async (versionId, reviewerIds, message) => {
    set({ isSubmitting: true, error: null });
    try {
      await api.post(`versions/${versionId}/reviews/`, {
        reviewer_ids: reviewerIds,
        message,
      });
      set({ isSubmitting: false });
      await get().fetchRequests(versionId);
      return true;
    } catch (err) {
      set({ isSubmitting: false, error: messageOf(err) });
      return false;
    }
  },

  cancelRequest: async (versionId, reviewId) => {
    try {
      await api.post(`versions/${versionId}/reviews/${reviewId}/cancel/`);
      await get().fetchRequests(versionId);
      return true;
    } catch (err) {
      set({ error: messageOf(err) });
      return false;
    }
  },

  fetchAssignments: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get('me/review_assignments/');
      set({ assignments: data.results, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: messageOf(err) });
    }
  },

  fetchContext: async (versionId) => {
    try {
      const { data } = await api.get(`versions/${versionId}/review_context/`);
      set({ context: data });
    } catch {
      set({ context: null });
    }
  },

  fetchMembers: async (projectId) => {
    try {
      const { data } = await api.get(`projects/${projectId}/members/`);
      set({ members: data.results });
    } catch (err) {
      set({ error: messageOf(err) });
    }
  },
}));
