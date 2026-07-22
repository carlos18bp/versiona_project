'use client';

/** E3: check results with evidence for one version (pinned config — I8). */

import { useEffect, useState } from 'react';

import { StatusBadge, type StatusBadgeVariant } from '@/components/ui/StatusBadge';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { api } from '@/lib/services/http';

interface CheckResultRow {
  key: string;
  label: string;
  outcome: 'pass' | 'warn' | 'fail';
  evidence: {
    section?: string;
    page?: number;
    snippet?: string;
    reason?: string;
    expected?: string;
  };
  message: string;
}

interface ChecksResponse {
  summary: { pass: number; warn: number; fail: number } | null;
  config_version: number;
  results: CheckResultRow[];
}

const OUTCOME_VARIANT: Record<CheckResultRow['outcome'], StatusBadgeVariant> = {
  pass: 'approved',
  warn: 'draft',
  fail: 'failed',
};

export function ChecksPanel({ versionId }: { versionId: string }) {
  const t = useDict('checks');
  const [data, setData] = useState<ChecksResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    void api
      .get<ChecksResponse>(`versions/${versionId}/checks/`)
      .then(({ data: payload }) => {
        if (!cancelled) setData(payload);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [versionId]);

  if (!data) return null;

  return (
    <section data-testid="checks-panel" className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">{t.title}</h2>
        <span className="text-xs text-muted-foreground">
          {interpolate(t.configVersion, { n: data.config_version })}
        </span>
      </div>

      {data.summary === null ? (
        <p className="text-xs text-muted-foreground">{t.empty}</p>
      ) : (
        <>
          <div data-testid="checks-summary" className="flex gap-2 text-xs">
            <StatusBadge variant="approved">✓ {data.summary.pass}</StatusBadge>
            <StatusBadge variant="draft">⚠ {data.summary.warn}</StatusBadge>
            <StatusBadge variant="failed">✗ {data.summary.fail}</StatusBadge>
          </div>
          <ol className="flex flex-col gap-1.5">
            {data.results.map((result) => (
              <li
                key={result.key}
                data-testid={`check-${result.key}`}
                data-outcome={result.outcome}
                className="rounded-xl border border-border bg-card px-3 py-2"
              >
                <div className="flex items-center justify-between gap-2 text-sm">
                  <span className="truncate">{result.label}</span>
                  <StatusBadge variant={OUTCOME_VARIANT[result.outcome]}>
                    {t.outcome[result.outcome]}
                  </StatusBadge>
                </div>
                {result.evidence.section ? (
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {t.evidenceIn} {result.evidence.section}
                    {result.evidence.page ? ` (${t.page} ${result.evidence.page})` : ''}
                    {result.evidence.snippet ? ` — “…${result.evidence.snippet}…”` : ''}
                  </p>
                ) : result.message ? (
                  <p className="mt-0.5 text-xs text-muted-foreground">{result.message}</p>
                ) : null}
              </li>
            ))}
          </ol>
        </>
      )}
    </section>
  );
}
