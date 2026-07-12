'use client';

const VARIANT_CLASSES: Record<StatusBadgeVariant, string> = {
  neutral: 'bg-muted text-muted-foreground border-border',
  draft: 'bg-muted text-foreground border-border',
  in_review: 'bg-primary/10 text-primary border-primary/30',
  with_observations: 'bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30',
  approved: 'bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30',
  failed: 'bg-destructive/10 text-destructive border-destructive/30',
};

export function StatusBadge({ variant = 'neutral', children }: StatusBadgeProps) {
  return (
    <span
      data-testid="status-badge"
      data-variant={variant}
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${VARIANT_CLASSES[variant]}`}
    >
      {children}
    </span>
  );
}

export type StatusBadgeVariant =
  | 'neutral'
  | 'draft'
  | 'in_review'
  | 'with_observations'
  | 'approved'
  | 'failed';

interface StatusBadgeProps {
  variant?: StatusBadgeVariant;
  children: React.ReactNode;
}
