/**
 * Bounding-box contract with the backend (docs/plan/04 §3): normalized 0–1,
 * top-left origin. Pure functions — the highlight overlays and the section
 * sync depend on these, so they carry the 90% coverage gate.
 */

export interface NormalizedBBox {
  page: number;
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

export interface CssBox {
  left: number;
  top: number;
  width: number;
  height: number;
}

/** Converts a normalized bbox to CSS pixels for a rendered page. */
export function bboxToCss(bbox: NormalizedBBox, pageWidth: number, pageHeight: number): CssBox {
  const left = clamp01(Math.min(bbox.x0, bbox.x1)) * pageWidth;
  const top = clamp01(Math.min(bbox.y0, bbox.y1)) * pageHeight;
  const width = Math.abs(clamp01(bbox.x1) - clamp01(bbox.x0)) * pageWidth;
  const height = Math.abs(clamp01(bbox.y1) - clamp01(bbox.y0)) * pageHeight;
  return { left, top, width, height };
}

export function clamp01(value: number): number {
  if (Number.isNaN(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

/** Groups bboxes by page so each page layer only renders its own. */
export function groupByPage(bboxes: NormalizedBBox[]): Map<number, NormalizedBBox[]> {
  const map = new Map<number, NormalizedBBox[]>();
  for (const bbox of bboxes) {
    const list = map.get(bbox.page) ?? [];
    list.push(bbox);
    map.set(bbox.page, list);
  }
  return map;
}

/** First page a set of bboxes touches (used to jump the viewer to a section). */
export function firstPage(bboxes: NormalizedBBox[]): number | null {
  if (bboxes.length === 0) return null;
  return bboxes.reduce((min, bbox) => Math.min(min, bbox.page), Number.POSITIVE_INFINITY);
}
