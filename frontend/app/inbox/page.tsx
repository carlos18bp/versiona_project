'use client';

import Link from 'next/link';
import { useEffect } from 'react';

import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { useNotificationStore } from '@/lib/stores/notificationStore';

function formatDate(iso: string) {
  return new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' }).format(
    new Date(iso)
  );
}

export default function InboxPage() {
  const { isAuthenticated } = useRequireAuth();
  const t = useDict('notifications');
  const common = useDict('common');
  const items = useNotificationStore((s) => s.items);
  const unread = useNotificationStore((s) => s.unread);
  const isLoading = useNotificationStore((s) => s.isLoading);
  const error = useNotificationStore((s) => s.error);
  const fetch = useNotificationStore((s) => s.fetch);
  const markRead = useNotificationStore((s) => s.markRead);
  const markAllRead = useNotificationStore((s) => s.markAllRead);

  useEffect(() => {
    if (isAuthenticated) void fetch();
  }, [isAuthenticated, fetch]);

  if (!isAuthenticated) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">
          {t.title}
          {unread > 0 ? (
            <span className="ml-2 text-sm font-normal text-muted-foreground">
              {unread} {t.unread}
            </span>
          ) : null}
        </h1>
        {unread > 0 ? (
          <button
            data-testid="mark-all-read"
            className="rounded-full border border-border px-4 py-1.5 text-sm hover:bg-accent"
            onClick={() => void markAllRead()}
            type="button"
          >
            {t.markAll}
          </button>
        ) : null}
      </div>

      <div className="mt-6">
        <AsyncBoundary
          isLoading={isLoading && items.length === 0}
          error={error}
          isEmpty={!isLoading && !error && items.length === 0}
          onRetry={() => void fetch()}
          retryLabel={common.retry}
          emptyTitle={t.empty}
          emptyDescription={t.emptyBody}
        >
          <ol data-testid="inbox-list" className="flex flex-col gap-2">
            {items.map((item) => (
              <li key={item.public_id}>
                <Link
                  data-testid={`inbox-item-${item.event_key}`}
                  className={`block rounded-2xl border p-4 transition-colors hover:bg-accent ${
                    item.read_at ? 'border-border bg-card opacity-70' : 'border-primary/40 bg-card'
                  }`}
                  href={item.link || '#'}
                  onClick={() => void markRead(item.public_id)}
                >
                  <p className="font-medium">{item.title}</p>
                  {item.body ? (
                    <p className="mt-0.5 text-sm text-muted-foreground">{item.body}</p>
                  ) : null}
                  <p className="mt-1 text-xs text-muted-foreground">{formatDate(item.created_at)}</p>
                </Link>
              </li>
            ))}
          </ol>
        </AsyncBoundary>
      </div>
    </main>
  );
}
