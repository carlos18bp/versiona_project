'use client';

import { useParams, useRouter, useSearchParams } from 'next/navigation';

import { CompareView, type CompareViewMode } from '@/components/compare/CompareView';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';

const MODES: CompareViewMode[] = ['side', 'sections', 'summary'];

export default function ComparePage() {
  const { isAuthenticated } = useRequireAuth();
  const params = useParams<{ docId: string; baseId: string; targetId: string }>();
  const search = useSearchParams();
  const router = useRouter();

  if (!isAuthenticated) return null;

  const requested = search.get('view') as CompareViewMode | null;
  const view: CompareViewMode = requested && MODES.includes(requested) ? requested : 'side';

  return (
    <main className="mx-auto max-w-7xl px-6 py-10">
      <CompareView
        documentId={params.docId}
        fromVersionId={params.baseId}
        toVersionId={params.targetId}
        view={view}
        onViewChange={(next) => {
          const query = new URLSearchParams(search.toString());
          query.set('view', next);
          router.replace(`?${query.toString()}`, { scroll: false });
        }}
      />
    </main>
  );
}
