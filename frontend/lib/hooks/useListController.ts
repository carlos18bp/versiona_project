'use client';

/**
 * Foundational list state (docs/plan mission — screen-state checklist):
 * loading / error+retry / pagination / debounced search over any fetcher
 * that returns the DRF paginated shape. Every list screen composes this with
 * <AsyncBoundary> + <DataTable> so the mandatory states are uniform.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ListParams {
  page: number;
  search: string;
}

type Fetcher<T> = (params: ListParams) => Promise<PaginatedResponse<T>>;

export function useListController<T>(fetcher: Fetcher<T>, debounceMs = 300) {
  const [items, setItems] = useState<T[]>([]);
  const [count, setCount] = useState(0);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [search, setSearch] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const requestSeq = useRef(0);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, debounceMs);
    return () => clearTimeout(timer);
  }, [search, debounceMs]);

  const load = useCallback(async () => {
    const seq = ++requestSeq.current;
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetcher({ page, search: debouncedSearch });
      if (seq !== requestSeq.current) return;
      setItems(data.results);
      setCount(data.count);
      setHasNext(Boolean(data.next));
    } catch (err) {
      if (seq !== requestSeq.current) return;
      const message =
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
        (err as Error)?.message ??
        'error';
      setError(message);
    } finally {
      if (seq === requestSeq.current) setIsLoading(false);
    }
  }, [fetcher, page, debouncedSearch]);

  useEffect(() => {
    void load();
  }, [load]);

  return {
    items,
    count,
    page,
    hasNext,
    hasPrevious: page > 1,
    search,
    isLoading,
    error,
    isEmpty: !isLoading && !error && items.length === 0 && debouncedSearch === '',
    setSearch,
    nextPage: () => setPage((p) => p + 1),
    previousPage: () => setPage((p) => Math.max(1, p - 1)),
    retry: load,
    reload: load,
  };
}

export type ListController<T> = ReturnType<typeof useListController<T>>;
