'use client';

/** D2 'already reviewed by you': what changed since MY last seal — the banner
 * that turns a re-review into a five-minute job. */

import { useEffect } from 'react';

import { StatusBadge } from '@/components/ui/StatusBadge';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { useReviewStore } from '@/lib/stores/reviewStore';

interface ReviewContextBarProps {
  versionId: string;
  onJumpToSection?: (stableKey: string) => void;
}

export function ReviewContextBar({ versionId, onJumpToSection }: ReviewContextBarProps) {
  const t = useDict('reviews');
  const context = useReviewStore((s) => s.context);
  const fetchContext = useReviewStore((s) => s.fetchContext);

  useEffect(() => {
    void fetchContext(versionId);
  }, [versionId, fetchContext]);

  if (!context || context.my_last_sealed_version === null) return null;

  return (
    <aside
      data-testid="review-context-bar"
      className="rounded-2xl border border-primary/40 bg-primary/5 p-4"
    >
      <h3 className="text-sm font-medium">{t.contextTitle}</h3>
      <p className="mt-0.5 text-xs text-muted-foreground">
        {interpolate(t.contextBody, { version: context.my_last_sealed_version })}
      </p>
      {context.changed.length > 0 ? (
        <div className="mt-2">
          <p className="text-xs font-medium text-muted-foreground">{t.contextChanged}:</p>
          <ul className="mt-1 flex flex-wrap gap-1">
            {context.changed.map((section) => (
              <li key={section.stable_key}>
                <button
                  data-testid={`context-changed-${section.stable_key}`}
                  className="rounded-full border border-amber-500/60 bg-amber-500/10 px-2.5 py-1 text-xs hover:bg-amber-500/20"
                  onClick={() => onJumpToSection?.(section.stable_key)}
                  type="button"
                >
                  {section.heading}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {context.unchanged.length > 0 ? (
        <p className="mt-2 text-xs text-muted-foreground">
          <StatusBadge variant="approved">{context.unchanged.length}</StatusBadge>{' '}
          {t.contextUnchanged}
        </p>
      ) : null}
    </aside>
  );
}
