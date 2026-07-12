'use client';

import { useParams } from 'next/navigation';
import { useCallback } from 'react';

import { UploadDropzone } from '@/components/versions/UploadDropzone';
import { VersionTimeline } from '@/components/versions/VersionTimeline';
import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { useDict } from '@/lib/i18n/dictionaries';
import { useListController } from '@/lib/hooks/useListController';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { api } from '@/lib/services/http';
import type { VersionSummary } from '@/lib/types';

export default function DocumentTimelinePage() {
  const { isAuthenticated } = useRequireAuth();
  const params = useParams<{ projectId: string; docId: string }>();
  const t = useDict('documents');
  const common = useDict('common');

  const fetcher = useCallback(
    async ({ page }: { page: number; search: string }) => {
      const { data } = await api.get(`documents/${params.docId}/versions/`, {
        params: { page },
      });
      return data;
    },
    [params.docId]
  );

  const list = useListController<VersionSummary>(fetcher);

  if (!isAuthenticated) return null;

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="text-2xl font-semibold">{t.versions}</h1>

      <div className="mt-6 flex flex-col gap-6">
        <UploadDropzone documentId={params.docId} compact onUploaded={list.reload} />

        <AsyncBoundary
          isLoading={list.isLoading}
          error={list.error}
          isEmpty={list.isEmpty}
          onRetry={list.retry}
          retryLabel={common.retry}
          emptyTitle={t.timelineEmpty}
        >
          <VersionTimeline
            projectId={params.projectId}
            documentId={params.docId}
            versions={list.items}
            canEdit
            onChanged={list.reload}
          />
          {list.hasNext || list.hasPrevious ? (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <button
                className="rounded-full border border-border px-4 py-1.5 disabled:opacity-40"
                disabled={!list.hasPrevious}
                onClick={list.previousPage}
                type="button"
              >
                {common.previous}
              </button>
              <span>
                {common.page} {list.page}
              </span>
              <button
                className="rounded-full border border-border px-4 py-1.5 disabled:opacity-40"
                disabled={!list.hasNext}
                onClick={list.nextPage}
                type="button"
              >
                {common.next}
              </button>
            </div>
          ) : null}
        </AsyncBoundary>
      </div>
    </main>
  );
}
