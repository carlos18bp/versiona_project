'use client';

/**
 * Document timeline (flow C3 — docs/audit/03 §9): version cards with author,
 * date (user timezone), message (editable while draft — I2b), traffic-light
 * placeholder, thumbnail, tombstones for trashed versions (C4) and the
 * approved badge.
 */

import Link from 'next/link';
import { useState } from 'react';

import { StatusBadge } from '@/components/ui/StatusBadge';
import { TypeToConfirmDialog } from '@/components/ui/TypeToConfirmDialog';
import { useToast } from '@/components/ui/toast';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { useVersionStore } from '@/lib/stores/versionStore';
import type { VersionSummary } from '@/lib/types';

interface VersionTimelineProps {
  projectId: string;
  documentId: string;
  versions: VersionSummary[];
  canEdit: boolean;
  onChanged: () => void;
}

function formatDate(iso: string) {
  try {
    return new Intl.DateTimeFormat('es', { dateStyle: 'medium', timeStyle: 'short' }).format(
      new Date(iso)
    );
  } catch {
    return iso;
  }
}

export function VersionTimeline({ projectId, documentId, versions, canEdit, onChanged }: VersionTimelineProps) {
  const t = useDict('documents');
  const common = useDict('common');
  const { toast } = useToast();
  const editMessage = useVersionStore((s) => s.editMessage);
  const trashVersion = useVersionStore((s) => s.trashVersion);
  const downloadUrl = useVersionStore((s) => s.downloadUrl);
  const [editing, setEditing] = useState<string | null>(null);
  const [draftMessage, setDraftMessage] = useState('');
  const [confirmTrash, setConfirmTrash] = useState<VersionSummary | null>(null);

  const download = async (version: VersionSummary) => {
    const url = await downloadUrl(version.public_id);
    if (url) window.open(url, '_blank', 'noopener');
  };

  const saveMessage = async (version: VersionSummary) => {
    const ok = await editMessage(version.public_id, draftMessage);
    if (ok) {
      toast(common.saved, 'success');
      setEditing(null);
      onChanged();
    } else {
      toast(t.messageFrozen, 'error');
    }
  };

  return (
    <ol data-testid="version-timeline" className="flex flex-col gap-3">
      {versions.map((version) => (
        <li
          key={version.public_id}
          data-testid={`version-item-${version.number}`}
          className={`rounded-2xl border p-4 ${
            version.is_trashed
              ? 'border-dashed border-border bg-muted/30 opacity-70'
              : 'border-border bg-card'
          }`}
        >
          {version.is_trashed ? (
            <p className="text-sm text-muted-foreground">
              v{version.number} — {t.deletedVersion}
            </p>
          ) : (
            <div className="flex items-start gap-4">
              {version.thumb_url ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={version.thumb_url}
                  alt={`v${version.number}`}
                  className="h-20 w-14 rounded-md border border-border object-cover"
                />
              ) : (
                <div className="flex h-20 w-14 items-center justify-center rounded-md border border-border bg-muted text-xs text-muted-foreground">
                  PDF
                </div>
              )}
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold">v{version.number}</span>
                  {version.is_approved ? (
                    <StatusBadge variant="approved">{t.approved}</StatusBadge>
                  ) : version.is_draft ? (
                    <StatusBadge variant="draft">{t.draft}</StatusBadge>
                  ) : null}
                  <StatusBadge
                    variant={
                      version.analysis_status === 'ready'
                        ? 'approved'
                        : version.analysis_status === 'failed'
                          ? 'failed'
                          : 'in_review'
                    }
                  >
                    {version.analysis_status === 'ready'
                      ? t.analysisDone
                      : version.analysis_status === 'failed'
                        ? t.analysisFailed
                        : t.analyzing}
                  </StatusBadge>
                  <span className="text-xs text-muted-foreground">
                    {t.scenario[version.source_scenario]} · {version.page_count} {t.pages}
                  </span>
                </div>
                {editing === version.public_id ? (
                  <div className="mt-2 flex gap-2">
                    <input
                      data-testid="edit-message-input"
                      className="w-full rounded-lg border border-border bg-background px-3 py-1.5 text-sm"
                      value={draftMessage}
                      onChange={(event) => setDraftMessage(event.target.value)}
                    />
                    <button
                      className="rounded-full bg-primary px-3 py-1.5 text-xs text-primary-foreground"
                      onClick={() => void saveMessage(version)}
                      type="button"
                    >
                      {common.save}
                    </button>
                    <button
                      className="rounded-full border border-border px-3 py-1.5 text-xs"
                      onClick={() => setEditing(null)}
                      type="button"
                    >
                      {common.cancel}
                    </button>
                  </div>
                ) : (
                  <p className="mt-1 truncate text-sm text-muted-foreground">
                    {version.message || '—'}
                    {canEdit && version.is_draft && !version.is_trashed ? (
                      <button
                        data-testid={`edit-message-${version.number}`}
                        className="ml-2 text-xs text-primary underline-offset-2 hover:underline"
                        onClick={() => {
                          setEditing(version.public_id);
                          setDraftMessage(version.message);
                        }}
                        type="button"
                        title={t.editMessage}
                      >
                        {t.editMessage}
                      </button>
                    ) : null}
                  </p>
                )}
                <p className="mt-1 text-xs text-muted-foreground">
                  {version.author_email ?? '—'} · {formatDate(version.created_at)}
                </p>
                {version.analysis_status === 'failed' && version.error_detail ? (
                  <p role="alert" className="mt-1 text-xs text-destructive">
                    {version.error_detail}
                  </p>
                ) : null}
              </div>
              <div className="flex shrink-0 flex-col items-end gap-1">
                <Link
                  className="text-xs text-primary underline-offset-2 hover:underline"
                  href={`/projects/${projectId}/documents/${documentId}/versions/${version.public_id}`}
                >
                  {t.viewer}
                </Link>
                <button
                  className="text-xs text-primary underline-offset-2 hover:underline"
                  onClick={() => void download(version)}
                  type="button"
                >
                  {t.download}
                </button>
                {canEdit && version.is_draft && !version.is_trashed ? (
                  <button
                    data-testid={`trash-version-${version.number}`}
                    className="text-xs text-destructive underline-offset-2 hover:underline"
                    onClick={() => setConfirmTrash(version)}
                    type="button"
                  >
                    {common.delete}
                  </button>
                ) : null}
              </div>
            </div>
          )}
        </li>
      ))}

      <TypeToConfirmDialog
        open={confirmTrash !== null}
        title={t.deleteVersionTitle}
        description={interpolate(t.deleteVersionBody, { n: confirmTrash?.number ?? 0 })}
        expectedText={`v${confirmTrash?.number ?? ''}`}
        confirmLabel={common.delete}
        cancelLabel={common.cancel}
        onClose={() => setConfirmTrash(null)}
        onConfirm={async () => {
          if (!confirmTrash) return;
          const ok = await trashVersion(confirmTrash.public_id);
          setConfirmTrash(null);
          if (ok) {
            toast(common.saved, 'success');
            onChanged();
          }
        }}
      />
    </ol>
  );
}
