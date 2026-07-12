'use client';

import { useCallback, useEffect, useState } from 'react';

import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/toast';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { api } from '@/lib/services/http';
import { useOrgStore } from '@/lib/stores/orgStore';
import type { TrashItem } from '@/lib/types';

const RESTORE_PATHS: Record<TrashItem['type'], (id: string) => string> = {
  project: (id) => `projects/${id}/restore/`,
  document: (id) => `documents/${id}/restore/`,
  version: (id) => `versions/${id}/restore/`,
};

export default function TrashPage() {
  const { isAuthenticated } = useRequireAuth();
  const t = useDict('trash');
  const common = useDict('common');
  const { toast } = useToast();
  const activeOrgId = useOrgStore((s) => s.activeOrgId);
  const fetchOrgs = useOrgStore((s) => s.fetchOrgs);
  const [items, setItems] = useState<TrashItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!activeOrgId) return;
    setIsLoading(true);
    setError(null);
    try {
      const { data } = await api.get(`orgs/${activeOrgId}/trash/`);
      setItems(data.results ?? []);
    } catch (err) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
          common.error
      );
    } finally {
      setIsLoading(false);
    }
  }, [activeOrgId, common.error]);

  useEffect(() => {
    if (isAuthenticated) void fetchOrgs();
  }, [isAuthenticated, fetchOrgs]);

  useEffect(() => {
    if (isAuthenticated && activeOrgId) void load();
  }, [isAuthenticated, activeOrgId, load]);

  if (!isAuthenticated) return null;

  const restore = async (item: TrashItem) => {
    try {
      await api.post(RESTORE_PATHS[item.type](item.public_id));
      toast(t.restored, 'success');
      void load();
    } catch (err) {
      toast(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
          common.error,
        'error'
      );
    }
  };

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-2xl font-semibold">{t.title}</h1>
      <div className="mt-6">
        <AsyncBoundary
          isLoading={isLoading}
          error={error}
          isEmpty={!isLoading && !error && items.length === 0}
          onRetry={load}
          retryLabel={common.retry}
          emptyTitle={t.emptyTitle}
          emptyDescription={t.emptyBody}
        >
          <ul data-testid="trash-list" className="flex flex-col gap-3">
            {items.map((item) => (
              <li
                key={`${item.type}-${item.public_id}`}
                className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4"
              >
                <StatusBadge variant="neutral">{t.type[item.type]}</StatusBadge>
                <div className="min-w-0 flex-1">
                  <p className="truncate font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.context}
                    {item.deleted_by ? ` · ${t.deletedBy} ${item.deleted_by}` : ''}
                    {item.purge_after
                      ? ` · ${t.purgeAfter} ${new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(new Date(item.purge_after))}`
                      : ''}
                  </p>
                </div>
                <button
                  data-testid={`restore-${item.type}`}
                  className="rounded-full border border-border px-4 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground"
                  onClick={() => void restore(item)}
                  type="button"
                >
                  {common.restore}
                </button>
              </li>
            ))}
          </ul>
        </AsyncBoundary>
      </div>
    </main>
  );
}
