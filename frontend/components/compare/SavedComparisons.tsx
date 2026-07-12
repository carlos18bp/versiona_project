'use client';

/** E2 — the project's named comparisons with deep links. */

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { useDict } from '@/lib/i18n/dictionaries';
import { api } from '@/lib/services/http';

interface SavedRow {
  public_id: string;
  name: string;
  created_by: string;
  document_title: string;
  summary: string;
  link: string;
}

export function SavedComparisons({ projectId }: { projectId: string }) {
  const t = useDict('savedComparisons');
  const [rows, setRows] = useState<SavedRow[]>([]);

  useEffect(() => {
    void api
      .get(`projects/${projectId}/saved_comparisons/`)
      .then(({ data }) => setRows(data.results))
      .catch(() => setRows([]));
  }, [projectId]);

  if (rows.length === 0) return null;

  return (
    <section data-testid="saved-comparisons" className="mt-10">
      <h2 className="text-lg font-semibold">{t.listTitle}</h2>
      <ul className="mt-3 flex flex-col gap-2">
        {rows.map((row) => (
          <li key={row.public_id}>
            <Link
              data-testid={`saved-${row.name}`}
              className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-card p-4 hover:bg-accent"
              href={row.link}
            >
              <div className="min-w-0">
                <p className="truncate font-medium">{row.name}</p>
                <p className="text-xs text-muted-foreground">
                  {row.document_title} · {row.summary} · {row.created_by}
                </p>
              </div>
              <span className="shrink-0 text-sm text-primary">{t.open}</span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
