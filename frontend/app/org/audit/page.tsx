'use client';

/** F3 base — the org audit log (owner/admin) with filters + CSV export. */

import { useCallback, useEffect, useState } from 'react';

import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { api } from '@/lib/services/http';
import { useOrgStore } from '@/lib/stores/orgStore';

interface AuditRow {
  event_type: string;
  actor_email: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

export default function OrgAuditPage() {
  const { isAuthenticated } = useRequireAuth();
  const t = useDict('orgAudit');
  const common = useDict('common');
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const fetchOrgs = useOrgStore((s) => s.fetchOrgs);
  const [rows, setRows] = useState<AuditRow[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ type: '', actor: '', from: '', to: '' });

  const buildQuery = useCallback(
    () =>
      Object.entries(filters)
        .filter(([, value]) => value)
        .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
        .join('&'),
    [filters]
  );

  const load = useCallback(async () => {
    if (!activeOrgId) return;
    setError(null);
    try {
      const { data } = await api.get(`orgs/${activeOrgId}/audit/?${buildQuery()}`);
      setRows(data.results);
    } catch (err) {
      setError(
        (err as { response?: { status?: number } })?.response?.status === 404
          ? 'La auditoría es una vista de administración de la organización.'
          : common.error
      );
    }
  }, [activeOrgId, buildQuery, common.error]);

  useEffect(() => {
    if (isAuthenticated) void fetchOrgs();
  }, [isAuthenticated, fetchOrgs]);

  useEffect(() => {
    if (isAuthenticated && activeOrgId) void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, activeOrgId]);

  if (!isAuthenticated) return null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">{t.title}</h1>
        <a
          data-testid="export-csv"
          className="rounded-full border border-border px-4 py-2 text-sm hover:bg-accent"
          href={`/api/orgs/${activeOrgId}/audit/?export=csv&${buildQuery()}`}
        >
          {t.exportCsv}
        </a>
      </div>

      <form
        className="mt-4 flex flex-wrap items-end gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          void load();
        }}
      >
        <label className="block text-sm">
          <span className="text-muted-foreground">{t.type}</span>
          <input
            data-testid="filter-type"
            className="mt-1 w-44 rounded-lg border border-border bg-background px-3 py-2"
            value={filters.type}
            onChange={(event) => setFilters({ ...filters, type: event.target.value })}
          />
        </label>
        <label className="block text-sm">
          <span className="text-muted-foreground">{t.actor}</span>
          <input
            data-testid="filter-actor"
            className="mt-1 w-44 rounded-lg border border-border bg-background px-3 py-2"
            value={filters.actor}
            onChange={(event) => setFilters({ ...filters, actor: event.target.value })}
          />
        </label>
        <label className="block text-sm">
          <span className="text-muted-foreground">{t.from}</span>
          <input
            type="date"
            className="mt-1 rounded-lg border border-border bg-background px-3 py-2"
            value={filters.from}
            onChange={(event) => setFilters({ ...filters, from: event.target.value })}
          />
        </label>
        <label className="block text-sm">
          <span className="text-muted-foreground">{t.to}</span>
          <input
            type="date"
            className="mt-1 rounded-lg border border-border bg-background px-3 py-2"
            value={filters.to}
            onChange={(event) => setFilters({ ...filters, to: event.target.value })}
          />
        </label>
        <button
          data-testid="apply-filters"
          className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
          type="submit"
        >
          {t.filter}
        </button>
      </form>

      <div className="mt-6">
        <AsyncBoundary
          isLoading={rows === null && !error}
          error={error}
          isEmpty={rows !== null && rows.length === 0}
          onRetry={() => void load()}
          retryLabel={common.retry}
          emptyTitle={t.empty}
        >
          <ol data-testid="audit-list" className="flex flex-col gap-1.5">
            {(rows ?? []).map((row, index) => (
              <li
                key={index}
                className="rounded-xl border border-border bg-card px-3 py-2 text-sm"
              >
                <span className="font-mono text-xs text-muted-foreground">
                  {new Date(row.created_at).toLocaleString('es')}
                </span>{' '}
                <span className="font-medium">{row.event_type}</span>{' '}
                <span className="text-muted-foreground">{row.actor_email ?? '—'}</span>
              </li>
            ))}
          </ol>
        </AsyncBoundary>
      </div>
    </main>
  );
}
