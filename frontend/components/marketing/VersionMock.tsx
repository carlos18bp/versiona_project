'use client';

import { useDict } from '@/lib/i18n/dictionaries';

/**
 * CSS-only stylized mini version-timeline + diff card for the hero.
 * Pure divs and design tokens — no image assets, dark mode for free.
 */
export function VersionMock() {
  const t = useDict('marketing');

  const rows = [
    { label: t.mockV3, current: true },
    { label: t.mockV2, current: false },
    { label: t.mockV1, current: false },
  ];

  return (
    <div
      className="rounded-2xl bg-card border border-border p-5 shadow-sm w-full max-w-sm"
      aria-hidden="true"
    >
      <p className="text-sm font-medium truncate">{t.mockDocTitle}</p>
      <ol className="mt-4 flex flex-col gap-3">
        {rows.map((row, index) => (
          <li key={row.label} className="flex items-start gap-3">
            <span className="relative flex flex-col items-center">
              <span
                className={`h-2.5 w-2.5 rounded-full mt-1 ${
                  row.current ? 'bg-primary' : 'bg-border'
                }`}
              />
              {index < rows.length - 1 ? (
                <span className="w-px h-6 bg-border" />
              ) : null}
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-muted-foreground truncate">{row.label}</p>
              {row.current ? (
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  <span className="inline-flex rounded-full bg-success/10 text-success text-[11px] px-2 py-0.5">
                    {t.mockSealsKept}
                  </span>
                  <span className="inline-flex rounded-full bg-warning/10 text-warning text-[11px] px-2 py-0.5">
                    {t.mockReReview}
                  </span>
                </div>
              ) : null}
            </div>
          </li>
        ))}
      </ol>
      <div className="mt-4 rounded-lg border border-border bg-background p-3 flex flex-col gap-1.5">
        <span className="h-2 w-3/4 rounded bg-muted" />
        <span className="h-2 w-full rounded bg-success/30" />
        <span className="h-2 w-5/6 rounded bg-destructive/30" />
        <span className="h-2 w-2/3 rounded bg-muted" />
      </div>
    </div>
  );
}
