'use client';

/** D1: the review request panel — open state, assignment progress, and the
 * request modal with the MANUAL reviewer picker (DP-A7). */

import { useEffect, useState } from 'react';

import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/toast';
import { useDict } from '@/lib/i18n/dictionaries';
import { useReviewStore } from '@/lib/stores/reviewStore';

interface ReviewRequestPanelProps {
  versionId: string;
  projectId: string;
  /** editors/admins can request; the panel is read-only otherwise */
  canRequest: boolean;
}

export function ReviewRequestPanel({ versionId, projectId, canRequest }: ReviewRequestPanelProps) {
  const t = useDict('reviews');
  const common = useDict('common');
  const { toast } = useToast();
  const requests = useReviewStore((s) => s.requests);
  const members = useReviewStore((s) => s.members);
  const isSubmitting = useReviewStore((s) => s.isSubmitting);
  const fetchRequests = useReviewStore((s) => s.fetchRequests);
  const fetchMembers = useReviewStore((s) => s.fetchMembers);
  const createRequest = useReviewStore((s) => s.createRequest);
  const cancelRequest = useReviewStore((s) => s.cancelRequest);
  const [modalOpen, setModalOpen] = useState(false);
  const [picked, setPicked] = useState<number[]>([]);
  const [message, setMessage] = useState('');

  useEffect(() => {
    void fetchRequests(versionId);
  }, [versionId, fetchRequests]);

  const open = requests.find((request) => request.status === 'open');
  const reviewers = members.filter((member) => ['reviewer', 'admin'].includes(member.role));

  const submit = async () => {
    const ok = await createRequest(versionId, picked, message.trim());
    if (ok) {
      toast(common.saved, 'success');
      setModalOpen(false);
      setPicked([]);
      setMessage('');
    } else {
      toast(useReviewStore.getState().error ?? common.error, 'error');
    }
  };

  return (
    <section data-testid="review-request-panel" className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-muted-foreground">{t.title}</h2>

      {open ? (
        <article className="rounded-2xl border border-border bg-card p-4">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge variant="in_review">{t.open}</StatusBadge>
            <span className="text-xs text-muted-foreground">
              {t.requestedBy} {open.requested_by_email}
            </span>
          </div>
          {open.message ? <p className="mt-1 text-sm">{open.message}</p> : null}
          <ul className="mt-2 flex flex-col gap-1 text-xs">
            {open.assignments.map((assignment) => (
              <li
                key={assignment.reviewer_email}
                data-testid={`assignment-${assignment.reviewer_email}`}
                className="flex items-center gap-2"
              >
                <StatusBadge variant={assignment.status === 'done' ? 'approved' : 'draft'}>
                  {assignment.status === 'done' ? t.doneBy : t.pendingOf}
                </StatusBadge>
                {assignment.reviewer_email}
              </li>
            ))}
          </ul>
          {canRequest ? (
            <button
              data-testid="cancel-review"
              className="mt-2 text-xs text-destructive underline-offset-2 hover:underline"
              onClick={() =>
                void cancelRequest(versionId, open.public_id).then((ok) =>
                  toast(ok ? common.saved : (useReviewStore.getState().error ?? common.error),
                    ok ? 'success' : 'error')
                )
              }
              type="button"
            >
              {t.cancel}
            </button>
          ) : null}
        </article>
      ) : null}

      {!open && requests.length > 0 ? (
        <p className="text-xs text-muted-foreground">
          {t[requests[0].status as 'completed' | 'cancelled' | 'superseded']}
        </p>
      ) : null}

      {canRequest && !open ? (
        <button
          data-testid="request-review"
          className="self-start rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground"
          onClick={() => {
            void fetchMembers(projectId);
            setModalOpen(true);
          }}
          type="button"
        >
          {t.request}
        </button>
      ) : null}

      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title={t.requestTitle}>
        <p className="text-sm text-muted-foreground">{t.pickReviewers}</p>
        <div className="mt-2 flex max-h-52 flex-col gap-1 overflow-y-auto">
          {reviewers.length === 0 ? (
            <p className="text-sm text-muted-foreground">{t.noReviewers}</p>
          ) : (
            reviewers.map((member) => (
              <label
                key={member.id}
                className="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm hover:bg-accent"
              >
                <input
                  data-testid={`pick-reviewer-${member.email}`}
                  type="checkbox"
                  checked={picked.includes(member.id)}
                  onChange={() =>
                    setPicked((current) =>
                      current.includes(member.id)
                        ? current.filter((id) => id !== member.id)
                        : [...current, member.id]
                    )
                  }
                />
                {member.email}
                <span className="text-xs text-muted-foreground">({member.role})</span>
              </label>
            ))
          )}
        </div>
        <label className="mt-3 block text-sm">
          <span className="text-muted-foreground">{t.message}</span>
          <input
            data-testid="review-message"
            className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
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
            data-testid="send-review-request"
            className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
            disabled={picked.length === 0 || isSubmitting}
            onClick={() => void submit()}
            type="button"
          >
            {t.send}
          </button>
        </div>
      </Modal>
    </section>
  );
}
