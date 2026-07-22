'use client';

import { create } from 'zustand';

interface UpgradeDialogState {
  isOpen: boolean;
  detail: string | null;
  show: (detail?: string | null) => void;
  hide: () => void;
}

export const useUpgradeDialogStore = create<UpgradeDialogState>((set) => ({
  isOpen: false,
  detail: null,
  show: (detail = null) => set({ isOpen: true, detail }),
  hide: () => set({ isOpen: false, detail: null }),
}));

/**
 * Opens the upgrade dialog when the error is a plan-limit 402 (the backend
 * marks them with `upgrade: true`). Returns whether it handled the error so
 * call sites can skip their generic path. Deliberately NOT a global axios
 * interceptor: the three limit sites opt in, everything else keeps its flow.
 */
export function maybeShowUpgradeDialog(err: unknown): boolean {
  const response = (err as { response?: { status?: number; data?: { upgrade?: boolean; error?: string } } })?.response;
  if (response?.status === 402 && response.data?.upgrade === true) {
    useUpgradeDialogStore.getState().show(response.data.error ?? null);
    return true;
  }
  return false;
}
