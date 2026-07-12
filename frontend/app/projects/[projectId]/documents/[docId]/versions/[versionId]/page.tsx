'use client';

import dynamic from 'next/dynamic';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';

import { ObservationsPanel } from '@/components/observations/ObservationsPanel';
import { ReviewContextBar } from '@/components/reviews/ReviewContextBar';
import { ReviewRequestPanel } from '@/components/reviews/ReviewRequestPanel';
import { SealActionBar } from '@/components/seals/SealActionBar';
import { SealsPanel } from '@/components/seals/SealsPanel';
import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { Skeleton } from '@/components/ui/Skeleton';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { TypeToConfirmDialog } from '@/components/ui/TypeToConfirmDialog';
import { useToast } from '@/components/ui/toast';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { useAuthStore } from '@/lib/stores/authStore';
import { useSealStore, type SealSummary } from '@/lib/stores/sealStore';
import { useVersionStore } from '@/lib/stores/versionStore';
import type { NormalizedBBox } from '@/lib/pdf/coords';

const PdfViewer = dynamic(
  () => import('@/components/pdf/PdfViewer').then((m) => m.PdfViewer),
  { ssr: false, loading: () => <Skeleton className="h-[480px] w-full" /> }
);

export default function VersionViewerPage() {
  const { isAuthenticated } = useRequireAuth();
  const params = useParams<{ projectId: string; versionId: string }>();
  const t = useDict('documents');
  const seals = useDict('seals');
  const common = useDict('common');
  const { toast } = useToast();
  const detail = useVersionStore((s) => s.detail);
  const fileUrl = useVersionStore((s) => s.fileUrl);
  const isLoading = useVersionStore((s) => s.isLoading);
  const error = useVersionStore((s) => s.error);
  const fetchDetail = useVersionStore((s) => s.fetchDetail);
  const fetchFileUrl = useVersionStore((s) => s.fetchFileUrl);
  const revokeSeal = useSealStore((s) => s.revokeSeal);
  const userEmail = useAuthStore((s) => s.user?.email ?? null);
  const [withdrawing, setWithdrawing] = useState<SealSummary | null>(null);
  const [anchorHighlights, setAnchorHighlights] = useState<NormalizedBBox[]>([]);

  useEffect(() => {
    if (!isAuthenticated) return;
    void fetchDetail(params.versionId);
    void fetchFileUrl(params.versionId);
  }, [isAuthenticated, params.versionId, fetchDetail, fetchFileUrl]);

  if (!isAuthenticated) return null;

  const canSeal =
    ['reviewer', 'admin'].includes(detail?.effective_role ?? '') && !detail?.is_approved;

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
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
              {fileUrl ? (
                <PdfViewer
                  file={fileUrl}
                  highlights={anchorHighlights}
                  highlightKind="modified"
                  scrollToPage={anchorHighlights[0]?.page ?? null}
                />
              ) : (
                <Skeleton className="h-[480px] w-full" />
              )}
            </div>
            <aside className="flex w-full shrink-0 flex-col gap-6 lg:w-80">
              {['reviewer', 'admin'].includes(detail.effective_role ?? '') ? (
                <ReviewContextBar versionId={detail.public_id} />
              ) : null}
              {canSeal ? (
                <SealActionBar
                  versionId={detail.public_id}
                  sections={detail.sections}
                  onSealed={() => void fetchDetail(params.versionId)}
                />
              ) : null}
              <ReviewRequestPanel
                versionId={detail.public_id}
                projectId={params.projectId}
                canRequest={['editor', 'admin'].includes(detail.effective_role ?? '')}
              />
              <SealsPanel
                versionId={detail.public_id}
                canConfirmPlan={detail.effective_role === 'admin'}
                currentUserEmail={userEmail}
                onWithdraw={(seal) => setWithdrawing(seal)}
              />
              <ObservationsPanel
                versionId={detail.public_id}
                versionNumber={detail.number}
                sections={detail.sections}
                canCreate={['reviewer', 'admin'].includes(detail.effective_role ?? '')}
                canReply={detail.effective_role !== 'viewer'}
                currentUserEmail={userEmail}
                onSelectAnchor={(quads) => setAnchorHighlights(quads)}
              />
              <div>
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
              </div>
            </aside>
          </div>
        ) : null}
      </AsyncBoundary>

      <TypeToConfirmDialog
        open={withdrawing !== null}
        title={seals.withdraw}
        description={seals.withdrawConfirm}
        expectedText={`v${detail?.number ?? ''}`}
        confirmLabel={seals.withdraw}
        cancelLabel={common.cancel}
        onClose={() => setWithdrawing(null)}
        onConfirm={async () => {
          if (!withdrawing || !detail) return;
          const ok = await revokeSeal(detail.public_id, withdrawing.public_id);
          setWithdrawing(null);
          toast(ok ? common.saved : (useSealStore.getState().error ?? common.error),
            ok ? 'success' : 'error');
        }}
      />
    </main>
  );
}
