import {
  countsByType,
  displayHeading,
  isChanged,
  nextChanged,
  onlyChanged,
  sectionTarget,
  type SectionChange,
} from '../sync';

const change = (over: Partial<SectionChange> = {}): SectionChange => ({
  stable_key: 'objeto',
  heading_from: '1. OBJETO',
  heading_to: '1. OBJETO',
  change_type: 'unchanged',
  similarity: 1,
  order_index: 0,
  ...over,
});

describe('compare/sync (pure)', () => {
  it('isChanged treats unchanged as not changed', () => {
    expect(isChanged(change())).toBe(false);
    expect(isChanged(change({ change_type: 'modified' }))).toBe(true);
    expect(isChanged(change({ change_type: 'renamed_only' }))).toBe(true);
  });

  it('onlyChanged filters out unchanged sections', () => {
    const list = [change(), change({ stable_key: 'a', change_type: 'added' })];

    expect(onlyChanged(list).map((c) => c.stable_key)).toEqual(['a']);
  });

  it('nextChanged returns the first changed section when none is active', () => {
    const list = [change(), change({ stable_key: 'm', change_type: 'modified' })];

    expect(nextChanged(list, null)?.stable_key).toBe('m');
  });

  it('nextChanged wraps around the changed sections', () => {
    const list = [
      change({ stable_key: 'm1', change_type: 'modified' }),
      change({ stable_key: 'm2', change_type: 'removed' }),
    ];

    expect(nextChanged(list, 'm1')?.stable_key).toBe('m2');
    expect(nextChanged(list, 'm2')?.stable_key).toBe('m1');
  });

  it('nextChanged returns null when nothing changed', () => {
    expect(nextChanged([change()], null)).toBeNull();
  });

  it('countsByType tallies every change type', () => {
    const counts = countsByType([
      change(),
      change({ change_type: 'modified' }),
      change({ change_type: 'modified' }),
      change({ change_type: 'removed' }),
    ]);

    expect(counts).toEqual({
      unchanged: 1,
      modified: 2,
      added: 0,
      removed: 1,
      renamed_only: 0,
    });
  });

  it('displayHeading falls back to the old heading for removed sections', () => {
    expect(displayHeading(change({ heading_to: '', heading_from: '6. PLAZO' }))).toBe('6. PLAZO');
    expect(displayHeading(change({ heading_to: '', heading_from: '' }))).toBe('objeto');
  });

  it('sectionTarget maps each side to its first page', () => {
    const target = sectionTarget(
      [{ page: 2, x0: 0, y0: 0, x1: 1, y1: 1 }],
      [{ page: 3, x0: 0, y0: 0, x1: 1, y1: 1 }]
    );

    expect(target).toEqual({ fromPage: 2, toPage: 3 });
  });

  it('sectionTarget returns null for a side without bboxes (added/removed)', () => {
    expect(sectionTarget([], [{ page: 1, x0: 0, y0: 0, x1: 1, y1: 1 }])).toEqual({
      fromPage: null,
      toPage: 1,
    });
  });
});
