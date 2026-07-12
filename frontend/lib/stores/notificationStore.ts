'use client';

import { create } from 'zustand';

import { api } from '@/lib/services/http';

export interface NotificationItem {
  public_id: string;
  event_key: string;
  title: string;
  body: string;
  link: string;
  payload: Record<string, unknown>;
  read_at: string | null;
  created_at: string;
}

export interface NotificationPref {
  event_key: string;
  label_es: string;
  label_en: string;
  mandatory_in_app: boolean;
  in_app: boolean;
  email: boolean;
}

interface NotificationState {
  items: NotificationItem[];
  unread: number;
  preferences: NotificationPref[];
  isLoading: boolean;
  error: string | null;
  fetch: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  fetchPreferences: () => Promise<void>;
  updatePreference: (
    eventKey: string,
    channel: 'in_app' | 'email',
    enabled: boolean
  ) => Promise<boolean>;
}

export const useNotificationStore = create<NotificationState>((set, get) => ({
  items: [],
  unread: 0,
  preferences: [],
  isLoading: false,
  error: null,

  fetch: async () => {
    set({ isLoading: true, error: null });
    try {
      const { data } = await api.get('me/notifications/');
      set({ items: data.results, unread: data.unread, isLoading: false });
    } catch (err) {
      set({ isLoading: false, error: (err as Error).message });
    }
  },

  markRead: async (id) => {
    try {
      await api.post(`me/notifications/${id}/read/`);
      set((state) => ({
        items: state.items.map((item) =>
          item.public_id === id ? { ...item, read_at: new Date().toISOString() } : item
        ),
        unread: Math.max(0, state.unread - 1),
      }));
    } catch {
      // reading is best-effort; the list refresh will reconcile
    }
  },

  markAllRead: async () => {
    await api.post('me/notifications/read_all/');
    await get().fetch();
  },

  fetchPreferences: async () => {
    const { data } = await api.get('me/notification_preferences/');
    set({ preferences: data.preferences });
  },

  updatePreference: async (eventKey, channel, enabled) => {
    try {
      const { data } = await api.patch('me/notification_preferences/', {
        [eventKey]: { [channel]: enabled },
      });
      set({ preferences: data.preferences });
      return true;
    } catch (err) {
      set({
        error:
          (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
          'No se pudo guardar la preferencia',
      });
      await get().fetchPreferences();
      return false;
    }
  },
}));
