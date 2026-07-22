/**
 * Side-by-side synchronization BY SECTION, not by pixel (docs/plan/04 §3):
 * a section can sit on different pages on each side, so the two viewers are
 * aligned through the section's first page on each side. Pure + gated at 90%.
 */

import { firstPage, type NormalizedBBox } from '@/lib/pdf/coords';

export type ChangeType = 'unchanged' | 'modified' | 'added' | 'removed' | 'renamed_only';

export interface SectionChange {
  stable_key: string;
  heading_from: string;
  heading_to: string;
  change_type: ChangeType;
  similarity: number | null;
  order_index: number;
}

export interface SectionTarget {
  fromPage: number | null;
  toPage: number | null;
}

/** Where each side must scroll to show a given section. */
export function sectionTarget(
  bboxesFrom: NormalizedBBox[],
  bboxesTo: NormalizedBBox[]
): SectionTarget {
  return { fromPage: firstPage(bboxesFrom), toPage: firstPage(bboxesTo) };
}

export const CHANGED_TYPES: ChangeType[] = ['modified', 'added', 'removed', 'renamed_only'];

export function isChanged(change: SectionChange): boolean {
  return CHANGED_TYPES.includes(change.change_type);
}

export function onlyChanged(changes: SectionChange[]): SectionChange[] {
  return changes.filter(isChanged);
}

/** Next changed section after the active one (wraps around); null if none. */
export function nextChanged(
  changes: SectionChange[],
  activeKey: string | null
): SectionChange | null {
  const changed = onlyChanged(changes);
  if (changed.length === 0) return null;
  if (!activeKey) return changed[0];
  const index = changed.findIndex((change) => change.stable_key === activeKey);
  if (index === -1) return changed[0];
  return changed[(index + 1) % changed.length];
}

export function countsByType(changes: SectionChange[]): Record<ChangeType, number> {
  const counts: Record<ChangeType, number> = {
    unchanged: 0,
    modified: 0,
    added: 0,
    removed: 0,
    renamed_only: 0,
  };
  for (const change of changes) counts[change.change_type] += 1;
  return counts;
}

/** Heading shown for a section: the new one, falling back to the old (removed). */
export function displayHeading(change: SectionChange): string {
  return change.heading_to || change.heading_from || change.stable_key;
}
