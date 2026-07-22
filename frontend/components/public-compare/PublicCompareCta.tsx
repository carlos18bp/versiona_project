'use client';

import Link from 'next/link';

import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';

/** Persistent signup banner under the public comparator (no dismiss). */
export function PublicCompareCta() {
  const t = useDict('publicCompare');

  return (
    <div
      data-testid="public-compare-cta"
      className="sticky bottom-0 z-30 border-t border-primary/20 bg-card/95 backdrop-blur"
    >
      <div className="max-w-4xl mx-auto px-6 py-4 flex flex-wrap items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="text-sm font-medium">{t.ctaTitle}</p>
          <p className="text-xs text-muted-foreground">{t.ctaBody}</p>
        </div>
        <Link
          className="shrink-0 rounded-full bg-primary text-primary-foreground px-5 py-2.5 text-sm hover:bg-primary/90"
          href={ROUTES.SIGN_UP}
        >
          {t.ctaButton}
        </Link>
      </div>
    </div>
  );
}
