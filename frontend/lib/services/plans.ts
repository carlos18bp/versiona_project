'use client';

import { publicApi } from '@/lib/services/http';

export interface PublicPlanLimits {
  max_active_projects: number | null;
  max_members: number | null;
  history_days: number | null;
}

export interface PublicPlan {
  key: 'free' | 'pro' | 'enterprise';
  label: string;
  price_cop: number | null;
  limits: PublicPlanLimits;
}

export const TRIAL_DAYS = 14;

// Static mirror of the backend catalog (billing/models.py PLANS): the landing
// preview never depends on API availability and /precios falls back to it.
export const STATIC_PLANS: PublicPlan[] = [
  {
    key: 'free',
    label: 'Gratis',
    price_cop: 0,
    limits: { max_active_projects: 1, max_members: 2, history_days: 30 },
  },
  {
    key: 'pro',
    label: 'Pro',
    price_cop: 149000,
    limits: { max_active_projects: 20, max_members: 25, history_days: null },
  },
  {
    key: 'enterprise',
    label: 'Enterprise',
    price_cop: null,
    limits: { max_active_projects: null, max_members: null, history_days: null },
  },
];

export interface PublicPlansResult {
  plans: PublicPlan[];
  trialDays: number;
  fromFallback: boolean;
}

export async function fetchPublicPlans(): Promise<PublicPlansResult> {
  try {
    const { data } = await publicApi.get('public/plans/');
    return { plans: data.plans, trialDays: data.trial_days, fromFallback: false };
  } catch {
    return { plans: STATIC_PLANS, trialDays: TRIAL_DAYS, fromFallback: true };
  }
}

export function formatCop(value: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    maximumFractionDigits: 0,
  }).format(value);
}
