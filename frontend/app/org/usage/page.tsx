'use client';

/** F2 — usage vs plan limits with 80% warnings and the informative upgrade
 * CTA (Wompi deferred: DECISIÓN PENDIENTE until the operator's keys). */

import { useEffect, useState } from 'react';

import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { api } from '@/lib/services/http';
import { useOrgStore } from '@/lib/stores/orgStore';

interface UsageResponse {
  plan: string;
  plan_label: string;
  limits: {
    max_active_projects: number;
    max_members: number;
    history_days: number | null;
  };
  usage: { active_projects: number; members: number };
  warnings: Array<{ limit: string; used: number; max: number; at_capacity: boolean }>;
  upgrade_available: boolean;
}

function Meter({ label, used, max, warning }: {
  label: string;
  used: number;
  max: number;
  warning?: { at_capacity: boolean };
}) {
  const t = useDict('billing');
  const percent = Math.min(100, Math.round((used / max) * 100));
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center justify-between gap-2">
        <span className="text-sm">{label}</span>
        <span className="text-sm font-medium">
          {used} / {max}
        </span>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full ${percent >= 100 ? 'bg-destructive' : percent >= 80 ? 'bg-amber-500' : 'bg-primary'}`}
          style={{ width: `${percent}%` }}
        />
      </div>
      {warning ? (
        <p className="mt-1.5 text-xs">
          <StatusBadge variant={warning.at_capacity ? 'failed' : 'draft'}>
            {warning.at_capacity ? t.atCapacity : t.nearCapacity}
          </StatusBadge>
        </p>
      ) : null}
    </div>
  );
}

export default function OrgUsagePage() {
  const { isAuthenticated } = useRequireAuth();
  const t = useDict('billing');
  const common = useDict('common');
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const fetchOrgs = useOrgStore((s) => s.fetchOrgs);
  const [data, setData] = useState<UsageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isAuthenticated) void fetchOrgs();
  }, [isAuthenticated, fetchOrgs]);

  useEffect(() => {
    if (!isAuthenticated || !activeOrgId) return;
    void api
      .get<UsageResponse>(`orgs/${activeOrgId}/usage/`)
      .then(({ data: payload }) => setData(payload))
      .catch(() => setError(common.error));
  }, [isAuthenticated, activeOrgId, common.error]);

  if (!isAuthenticated) return null;

  const warningFor = (key: string) => data?.warnings.find((w) => w.limit === key);

  return (
    <main className="mx-auto max-w-2xl px-6 py-10">
      <h1 className="text-2xl font-semibold">{t.usageTitle}</h1>
      <div className="mt-6">
        <AsyncBoundary
          isLoading={!data && !error}
          error={error}
          onRetry={() => window.location.reload()}
          retryLabel={common.retry}
        >
          {data ? (
            <div data-testid="usage-panel" className="flex flex-col gap-4">
              <p className="text-sm">
                {t.plan}: <StatusBadge variant="in_review">{data.plan_label}</StatusBadge>
              </p>
              <Meter
                label={t.projects}
                used={data.usage.active_projects}
                max={data.limits.max_active_projects}
                warning={warningFor('max_active_projects')}
              />
              <Meter
                label={t.members}
                used={data.usage.members}
                max={data.limits.max_members}
                warning={warningFor('max_members')}
              />
              <p className="text-sm text-muted-foreground">
                {t.history}:{' '}
                {data.limits.history_days === null
                  ? t.historyUnlimited
                  : interpolate(t.historyDays, { days: data.limits.history_days })}
              </p>

              {data.upgrade_available ? (
                <div
                  data-testid="upgrade-cta"
                  className="rounded-2xl border border-primary/40 bg-primary/5 p-4"
                >
                  <h2 className="font-medium">{t.upgradeTitle}</h2>
                  <p className="mt-1 text-sm text-muted-foreground">{t.upgradeBody}</p>
                  <a
                    className="mt-3 inline-block rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
                    href="mailto:hola@versiona.app?subject=Plan%20Pro"
                  >
                    {t.upgradeCta}
                  </a>
                </div>
              ) : null}
            </div>
          ) : null}
        </AsyncBoundary>
      </div>
    </main>
  );
}
