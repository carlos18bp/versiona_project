'use client';

/**
 * Slim global banner while the org's Pro trial runs. Mirrors the staging
 * banner pattern: mounted once in the root layout, self-fetching, dismissable
 * per browser session (sessionStorage).
 */
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { ROUTES } from '@/lib/constants';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { useAuthStore } from '@/lib/stores/authStore';
import { useOrgStore } from '@/lib/stores/orgStore';
import { useTrialStore } from '@/lib/stores/trialStore';

const DISMISS_KEY = 'versiona-trial-banner-dismissed';

export function TrialBanner() {
  const t = useDict('billing');
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const trial = useTrialStore((s) => s.trial);
  const fetchTrial = useTrialStore((s) => s.fetch);
  const [dismissed, setDismissed] = useState(true);

  useEffect(() => {
    setDismissed(sessionStorage.getItem(DISMISS_KEY) === '1');
  }, []);

  useEffect(() => {
    if (isAuthenticated && activeOrgId) void fetchTrial(activeOrgId);
  }, [isAuthenticated, activeOrgId, fetchTrial]);

  if (!isAuthenticated || dismissed || !trial?.on_trial) return null;

  const days = trial.days_left ?? 0;
  const text =
    days === 1 ? t.trialBannerOne : interpolate(t.trialBannerMany, { days });

  return (
    <div
      data-testid="trial-banner"
      role="status"
      className="border-b border-primary/20 bg-primary/10 text-sm"
    >
      <div className="max-w-6xl mx-auto px-6 py-2 flex items-center justify-between gap-3">
        <p>
          {text}{' '}
          <Link
            data-testid="trial-banner-plans"
            className="font-medium text-primary hover:underline"
            href={ROUTES.PRECIOS}
          >
            {t.trialBannerCta}
          </Link>
        </p>
        <button
          type="button"
          data-testid="trial-banner-dismiss"
          aria-label={t.trialBannerDismiss}
          className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          onClick={() => {
            sessionStorage.setItem(DISMISS_KEY, '1');
            setDismissed(true);
          }}
        >
          ✕
        </button>
      </div>
    </div>
  );
}
