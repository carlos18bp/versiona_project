'use client';

/** D3: anchored observation threads for a version — status filter, replies,
 * the I14 transitions and the anchor health per version. */

import { useEffect, useState } from 'react';

import { EmptyState } from '@/components/ui/EmptyState';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge, type StatusBadgeVariant } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/toast';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { useObservationStore, type ObservationRow } from '@/lib/stores/observationStore';
import type { SectionInfo } from '@/lib/types';

const STATUS_VARIANT: Record<ObservationRow['status'], StatusBadgeVariant> = {
  open: 'in_review',
  answered: 'draft',
  resolved: 'approved',
};

interface ObservationsPanelProps {
  versionId: string;
  versionNumber: number;
  sections: SectionInfo[];
  /** reviewers/admins create + resolve; editors reply; viewers read */
  canCreate: boolean;
  canReply: boolean;
  currentUserEmail?: string | null;
  onSelectAnchor?: (quads: ObservationRow['anchors'][number]['quads']) => void;
}

export function ObservationsPanel({
  versionId,
  versionNumber,
  sections,
  canCreate,
  canReply,
  currentUserEmail,
  onSelectAnchor,
}: ObservationsPanelProps) {
  const t = useDict('observations');
  const common = useDict('common');
  const { toast } = useToast();
  const items = useObservationStore((s) => s.items);
  const isSubmitting = useObservationStore((s) => s.isSubmitting);
  const fetch = useObservationStore((s) => s.fetch);
  const create = useObservationStore((s) => s.create);
  const reply = useObservationStore((s) => s.reply);
  const setStatus = useObservationStore((s) => s.setStatus);
  const [showResolved, setShowResolved] = useState(false);
  const [modalOpen, setModalOpen] = useState(false);
  const [body, setBody] = useState('');
  const [sectionKey, setSectionKey] = useState('');
  const [replyDrafts, setReplyDrafts] = useState<Record<string, string>>({});

  useEffect(() => {
    void fetch(versionId);
  }, [versionId, fetch]);

  const visible = items.filter((item) => showResolved || item.status !== 'resolved');

  const act = async (result: Promise<boolean>) => {
    const ok = await result;
    toast(ok ? common.saved : (useObservationStore.getState().error ?? common.error),
      ok ? 'success' : 'error');
    return ok;
  };

  const anchorFor = (item: ObservationRow) =>
    item.anchors.find((anchor) => anchor.version_number === versionNumber);

  return (
    <section data-testid="observations-panel" className="flex flex-col gap-2">
      <div className="flex items-center justify-between gap-2">
        <h2 className="text-sm font-semibold text-muted-foreground">{t.title}</h2>
        <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <input
            data-testid="show-resolved"
            type="checkbox"
            checked={showResolved}
            onChange={() => setShowResolved((value) => !value)}
          />
          {t.showResolved}
        </label>
      </div>

      {canCreate ? (
        <button
          data-testid="add-observation"
          className="self-start rounded-full border border-border px-4 py-1.5 text-sm hover:bg-accent"
          onClick={() => setModalOpen(true)}
          type="button"
        >
          {t.add}
        </button>
      ) : null}

      {visible.length === 0 ? (
        <EmptyState title={t.empty} description={t.emptyBody} />
      ) : (
        <ol className="flex flex-col gap-3">
          {visible.map((item) => {
            const anchor = anchorFor(item);
            return (
              <li
                key={item.public_id}
                data-testid={`observation-${item.public_id}`}
                data-status={item.status}
                className="rounded-2xl border border-border bg-card p-4"
              >
                <div className="flex flex-wrap items-center gap-2 text-sm">
                  <StatusBadge variant={STATUS_VARIANT[item.status]}>
                    {t.status[item.status]}
                  </StatusBadge>
                  <span className="font-medium">{item.author_email}</span>
                  <span className="text-xs text-muted-foreground">
                    {interpolate(t.onVersion, { version: item.created_on })}
                    {item.resolved_in
                      ? ` · ${interpolate(t.resolvedIn, { version: item.resolved_in })}`
                      : ''}
                  </span>
                </div>
                {item.section_heading ? (
                  <button
                    data-testid={`observation-anchor-${item.public_id}`}
                    className="mt-1 text-xs text-primary underline-offset-2 hover:underline"
                    onClick={() => anchor && onSelectAnchor?.(anchor.quads)}
                    type="button"
                  >
                    {item.section_heading}
                    {anchor ? ` — ${t.anchor[anchor.method]}` : ''}
                  </button>
                ) : null}
                <p className="mt-1 text-sm">{item.body}</p>

                {item.replies.map((replyRow) => (
                  <p
                    key={replyRow.public_id}
                    className="mt-2 rounded-xl bg-muted/40 px-3 py-2 text-sm"
                  >
                    <span className="font-medium">{replyRow.author_email}</span>: {replyRow.body}
                  </p>
                ))}

                <div className="mt-2 flex flex-wrap items-center gap-2">
                  {canReply && item.status !== 'resolved' ? (
                    <>
                      <input
                        data-testid={`reply-input-${item.public_id}`}
                        className="min-w-0 flex-1 rounded-lg border border-border bg-background px-3 py-1.5 text-sm"
                        placeholder={t.replyPlaceholder}
                        value={replyDrafts[item.public_id] ?? ''}
                        onChange={(event) =>
                          setReplyDrafts((current) => ({
                            ...current,
                            [item.public_id]: event.target.value,
                          }))
                        }
                      />
                      <button
                        data-testid={`reply-send-${item.public_id}`}
                        className="rounded-full border border-border px-3 py-1.5 text-xs hover:bg-accent"
                        onClick={() =>
                          void act(
                            reply(versionId, item.public_id, replyDrafts[item.public_id] ?? '')
                          ).then((ok) => {
                            if (ok)
                              setReplyDrafts((current) => ({ ...current, [item.public_id]: '' }));
                          })
                        }
                        type="button"
                      >
                        {t.reply}
                      </button>
                    </>
                  ) : null}
                  {item.status === 'answered' &&
                  (item.author_email === currentUserEmail || canCreate) ? (
                    <button
                      data-testid={`resolve-${item.public_id}`}
                      className="rounded-full bg-primary px-3 py-1.5 text-xs text-primary-foreground"
                      onClick={() => void act(setStatus(versionId, item.public_id, 'resolved'))}
                      type="button"
                    >
                      {t.resolve}
                    </button>
                  ) : null}
                  {item.status === 'resolved' && item.author_email === currentUserEmail ? (
                    <button
                      data-testid={`reopen-${item.public_id}`}
                      className="rounded-full border border-border px-3 py-1.5 text-xs hover:bg-accent"
                      onClick={() => void act(setStatus(versionId, item.public_id, 'open'))}
                      type="button"
                    >
                      {t.reopen}
                    </button>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      )}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t.addTitle}>
        <label className="block text-sm">
          <span className="text-muted-foreground">{t.section}</span>
          <select
            data-testid="observation-section"
            className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            value={sectionKey}
            onChange={(event) => setSectionKey(event.target.value)}
          >
            <option value="">—</option>
            {sections.map((section) => (
              <option key={section.stable_key} value={section.stable_key}>
                {section.heading_text}
              </option>
            ))}
          </select>
        </label>
        <label className="mt-3 block text-sm">
          <span className="text-muted-foreground">{t.body}</span>
          <textarea
            data-testid="observation-body"
            className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            rows={3}
            value={body}
            onChange={(event) => setBody(event.target.value)}
          />
        </label>
        <div className="mt-4 flex justify-end gap-2">
          <button
            className="rounded-full border border-border px-4 py-2 text-sm"
            onClick={() => setModalOpen(false)}
            type="button"
          >
            {common.cancel}
          </button>
          <button
            data-testid="observation-submit"
            className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
            disabled={!body.trim() || isSubmitting}
            onClick={() =>
              void act(create(versionId, { body: body.trim(), sectionKey })).then((ok) => {
                if (ok) {
                  setModalOpen(false);
                  setBody('');
                  setSectionKey('');
                }
              })
            }
            type="button"
          >
            {t.submit}
          </button>
        </div>
      </Modal>
    </section>
  );
}
