'use client';

/**
 * Uniform loading / error+retry / empty / content rendering — the mandatory
 * screen states of docs/audit/03 §9 in one place. No screen hand-rolls
 * `if (loading)` again.
 */

import { Skeleton } from './Skeleton';
import { EmptyState } from './EmptyState';

interface AsyncBoundaryProps {
  isLoading: boolean;
  error: string | null;
  isEmpty?: boolean;
  onRetry?: () => void;
  retryLabel?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
  skeleton?: React.ReactNode;
  children: React.ReactNode;
}

export function AsyncBoundary({
  isLoading,
  error,
  isEmpty = false,
  onRetry,
  retryLabel = 'Reintentar',
  emptyTitle = 'Nada por aquí',
  emptyDescription,
  emptyAction,
  skeleton,
  children,
}: AsyncBoundaryProps) {
  if (isLoading) {
    return (
      <div data-testid="async-loading" className="flex flex-col gap-3">
        {skeleton ?? (
          <>
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-2/3" />
          </>
        )}
      </div>
    );
  }

  if (error) {
    return (
      <div
        data-testid="async-error"
        className="flex flex-col items-center gap-3 rounded-2xl border border-destructive/30 bg-destructive/5 px-6 py-10 text-center"
      >
        <p className="text-sm text-destructive">{error}</p>
        {onRetry ? (
          <button
            className="rounded-full border border-border px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground"
            onClick={onRetry}
            type="button"
          >
            {retryLabel}
          </button>
        ) : null}
      </div>
    );
  }

  if (isEmpty) {
    return (
      <EmptyState title={emptyTitle} description={emptyDescription} action={emptyAction} />
    );
  }

  return <>{children}</>;
}
