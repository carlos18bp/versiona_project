'use client';

import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import { useEffect } from 'react';

import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { Skeleton } from '@/components/ui/Skeleton';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { useVersionStore } from '@/lib/stores/versionStore';

const PdfViewer = dynamic(
  () => import('@/components/pdf/PdfViewer').then((m) => m.PdfViewer),
  { ssr: false, loading: () => <Skeleton className="h-[480px] w-full" /> }
);

export default function VersionViewerPage() {
  const { isAuthenticated } = useRequireAuth();
  const params = useParams<{ versionId: string }>();
  const t = useDict('documents');
  const common = useDict('common');
  const detail = useVersionStore((s) => s.detail);
  const fileUrl = useVersionStore((s) => s.fileUrl);
  const isLoading = useVersionStore((s) => s.isLoading);
  const error = useVersionStore((s) => s.error);
  const fetchDetail = useVersionStore((s) => s.fetchDetail);
  const fetchFileUrl = useVersionStore((s) => s.fetchFileUrl);

  useEffect(() => {
    if (!isAuthenticated) return;
    void fetchDetail(params.versionId);
    void fetchFileUrl(params.versionId);
  }, [isAuthenticated, params.versionId, fetchDetail, fetchFileUrl]);

  if (!isAuthenticated) return null;

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <AsyncBoundary
        isLoading={isLoading && !detail}
        error={!detail ? error : null}
        onRetry={() => void fetchDetail(params.versionId)}
        retryLabel={common.retry}
      >
        {detail ? (
          <div className="flex flex-col gap-6 lg:flex-row">
            <div className="min-w-0 flex-1">
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <h1 className="text-xl font-semibold">
                  {t.version} v{detail.number}
                </h1>
                {detail.is_approved ? (
                  <StatusBadge variant="approved">{t.approved}</StatusBadge>
                ) : detail.is_draft ? (
                  <StatusBadge variant="draft">{t.draft}</StatusBadge>
                ) : null}
                <span className="text-sm text-muted-foreground">{detail.message}</span>
              </div>
              {fileUrl ? <PdfViewer file={fileUrl} /> : <Skeleton className="h-[480px] w-full" />}
            </div>
            <aside className="w-full shrink-0 lg:w-72">
              <h2 className="text-sm font-semibold text-muted-foreground">
                {detail.sections.length} {t.sections}
              </h2>
              <ol data-testid="sections-list" className="mt-3 flex flex-col gap-1">
                {detail.sections.map((section) => (
                  <li
                    key={section.stable_key}
                    className="rounded-lg border border-border bg-card px-3 py-2 text-sm"
                  >
                    <p className="truncate font-medium">{section.heading_text}</p>
                    <p className="text-xs text-muted-foreground">
                      {common.page} {section.page_start}
                      {section.page_end !== section.page_start ? `–${section.page_end}` : ''}
                    </p>
                  </li>
                ))}
              </ol>
            </aside>
          </div>
        ) : null}
      </AsyncBoundary>
    </main>
  );
}
