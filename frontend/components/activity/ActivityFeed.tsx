'use client';

/** Kit 6: project activity feed over whitelisted AuditEvents (no ip). */

import { useCallback, useEffect, useState } from 'react';

import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { api } from '@/lib/services/http';

interface ActivityRow {
  event_type: string;
  actor_email: string | null;
  payload: Record<string, unknown>;
  created_at: string;
}

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(iso)
  );
}

export function ActivityFeed({ projectId }: { projectId: string }) {
  const t = useDict('activity');
  const [rows, setRows] = useState<ActivityRow[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get(`projects/${projectId}/activity/`);
      setRows(data.results ?? []);
    } catch {
      setRows([]);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (isLoading) return null;

  return (
    <section data-testid="activity-feed" className="mt-10">
      <h2 className="text-lg font-semibold">{t.title}</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">{t.empty}</p>
      ) : (
        <ol className="mt-3 flex flex-col gap-1.5 border-l border-border pl-4">
          {rows.slice(0, 15).map((row, index) => {
            const template = t.event[row.event_type as keyof typeof t.event];
            const text = template
              ? interpolate(template, row.payload as Record<string, string | number>)
              : row.event_type;
            return (
              <li key={index} className="text-sm">
                <span className="font-medium">{row.actor_email ?? 'Versiona'}</span>{' '}
                <span>{text}</span>{' '}
                <span className="text-xs text-muted-foreground">{formatDate(row.created_at)}</span>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
