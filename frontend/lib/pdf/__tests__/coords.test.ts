import { bboxToCss, clamp01, firstPage, groupByPage } from '../coords';

describe('pdf/coords (pure)', () => {
  it('bboxToCss scales a normalized bbox to page pixels', () => {
    const css = bboxToCss({ page: 1, x0: 0.1, y0: 0.2, x1: 0.6, y1: 0.5 }, 400, 600);

    expect(css).toEqual({ left: 40, top: 120, width: 200, height: 180 });
  });

  it('bboxToCss normalizes inverted coordinates', () => {
    const css = bboxToCss({ page: 1, x0: 0.6, y0: 0.5, x1: 0.1, y1: 0.2 }, 400, 600);

    expect(css.left).toBe(40);
    expect(css.top).toBe(120);
    expect(css.width).toBe(200);
  });

  it('bboxToCss clamps out-of-range values', () => {
    const css = bboxToCss({ page: 1, x0: -0.5, y0: 0, x1: 1.5, y1: 1 }, 200, 100);

    expect(css.left).toBe(0);
    expect(css.width).toBe(200);
    expect(css.height).toBe(100);
  });

  it('clamp01 maps NaN to zero', () => {
    expect(clamp01(Number.NaN)).toBe(0);
    expect(clamp01(2)).toBe(1);
    expect(clamp01(-1)).toBe(0);
  });

  it('groupByPage buckets bboxes per page', () => {
    const grouped = groupByPage([
      { page: 1, x0: 0, y0: 0, x1: 1, y1: 1 },
      { page: 2, x0: 0, y0: 0, x1: 1, y1: 1 },
      { page: 1, x0: 0, y0: 0, x1: 1, y1: 1 },
    ]);

    expect(grouped.get(1)).toHaveLength(2);
    expect(grouped.get(2)).toHaveLength(1);
  });

  it('firstPage returns the lowest page touched', () => {
    expect(
      firstPage([
        { page: 3, x0: 0, y0: 0, x1: 1, y1: 1 },
        { page: 2, x0: 0, y0: 0, x1: 1, y1: 1 },
      ])
    ).toBe(2);
  });

  it('firstPage returns null with no bboxes', () => {
    expect(firstPage([])).toBeNull();
  });
});
