'use client';

/**
 * Trimmed result view for anonymous comparisons: counts header + the shared
 * SectionChangeList + an inline word-diff pane. No PDF panes — the uploaded
 * files are deleted server-side right after processing.
 */
import { useMemo, useState } from 'react';

import { SectionChangeList } from '@/components/compare/SectionChangeList';
import { countsByType, isChanged, type SectionChange } from '@/lib/compare/sync';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import type {
  PublicCompareSection,
  PublicComparisonDetail,
} from '@/lib/stores/publicCompareStore';

const COUNT_TILES = [
  { key: 'modified', testid: 'count-modified' },
  { key: 'added', testid: 'count-added' },
  { key: 'removed', testid: 'count-removed' },
  { key: 'unchanged', testid: 'count-unchanged' },
] as const;

export function PublicCompareResult({ detail }: { detail: PublicComparisonDetail }) {
  const t = useDict('publicCompare');
  const compare = useDict('compare');
  const [activeKey, setActiveKey] = useState<string | null>(null);
  const [hideUnchanged, setHideUnchanged] = useState(true);

  const sections = useMemo(
    () => detail.result?.sections ?? [],
    [detail.result?.sections]
  );
  const counts = detail.result?.counts ?? countsByType(sections as SectionChange[]);
  const active: PublicCompareSection | undefined = sections.find(
    (section) => section.stable_key === activeKey
  );

  const countLabels: Record<(typeof COUNT_TILES)[number]['key'], string> = {
    modified: compare.change.modified,
    added: compare.change.added,
    removed: compare.change.removed,
    unchanged: compare.change.unchanged,
  };

  return (
    <section data-testid="public-compare-result" className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{t.resultTitle}</h1>
        <p className="mt-1 text-sm text-muted-foreground" data-testid="public-files-line">
          {interpolate(t.filesCompared, {
            a: detail.file_a_name,
            b: detail.file_b_name,
          })}
        </p>
        <p className="mt-1 text-sm">{detail.result?.summary_text}</p>
      </div>

      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {COUNT_TILES.map(({ key, testid }) => (
          <div key={key} className="rounded-2xl border border-border bg-card p-4">
            <dt className="text-xs text-muted-foreground">{countLabels[key]}</dt>
            <dd data-testid={testid} className="mt-1 text-2xl font-semibold">
              {counts[key] ?? 0}
            </dd>
          </div>
        ))}
      </dl>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        <SectionChangeList
          changes={sections}
          activeKey={activeKey}
          hideUnchanged={hideUnchanged}
          onToggleHideUnchanged={() => setHideUnchanged((v) => !v)}
          onSelect={(key) => setActiveKey(key)}
        />
        <div className="rounded-2xl border border-border bg-card p-5 min-h-40">
          {active?.word_diff?.length ? (
            <>
              <p className="text-sm font-medium">{t.sectionDetail}</p>
              <p
                data-testid="public-word-diff"
                className="mt-3 text-sm leading-relaxed whitespace-pre-wrap"
              >
                {active.word_diff.map((op, index) =>
                  op.op === 'insert' ? (
                    <ins
                      key={index}
                      className="bg-success/15 text-success no-underline rounded px-0.5"
                    >
                      {op.text}
                    </ins>
                  ) : op.op === 'delete' ? (
                    <del key={index} className="bg-destructive/10 text-destructive rounded px-0.5">
                      {op.text}
                    </del>
                  ) : (
                    <span key={index}>{op.text}</span>
                  )
                )}
              </p>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              {sections.filter(isChanged).length === 0
                ? compare.noChanges
                : t.sectionDetail}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
