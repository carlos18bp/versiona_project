'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';

import { useAuthStore } from '@/lib/stores/authStore';
import { useMounted } from '@/lib/hooks/useMounted';

/**
 * Auth gate for a client page, hydration-safe.
 *
 * The store seeds `isAuthenticated` from a cookie through js-cookie, which is
 * browser-only: the server always computes `false`, the client `true` for a
 * signed-in visitor. Every one of the 19 pages using this hook does
 * `if (!isAuthenticated) return null`, so the server rendered nothing while the
 * client rendered the page — a hydration mismatch on EVERY authenticated page,
 * after which React discards the server HTML and re-renders the tree.
 *
 * The returned flag therefore stays `false` until mounted, so the server and the
 * first client render agree; the page then appears in a deliberate second
 * render. The REDIRECT deliberately reads the raw store value instead, gated on
 * `mounted` — routing an authenticated visitor to /sign-in just because the
 * component had not mounted yet would be a real bug, not a cosmetic one.
 */
export const useRequireAuth = () => {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const syncFromCookies = useAuthStore((s) => s.syncFromCookies);
  const mounted = useMounted();

  useEffect(() => {
    syncFromCookies();
  }, [syncFromCookies]);

  useEffect(() => {
    if (mounted && !isAuthenticated) {
      router.replace('/sign-in');
    }
  }, [mounted, isAuthenticated, router]);

  return { isAuthenticated: mounted && isAuthenticated };
};
