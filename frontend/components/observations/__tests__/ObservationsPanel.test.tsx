import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ObservationsPanel } from '../ObservationsPanel';
import type { ObservationRow } from '../../../lib/stores/observationStore';

const fetch = jest.fn();
const create = jest.fn();
const reply = jest.fn();
const setStatus = jest.fn();
let items: ObservationRow[] = [];

jest.mock('../../../lib/stores/observationStore', () => ({
  useObservationStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ items, isSubmitting: false, error: null, fetch, create, reply, setStatus }),
    { getState: () => ({ error: null }) }
  ),
}));

const observation = (over: Partial<ObservationRow> = {}): ObservationRow => ({
  public_id: 'o1',
  body: 'La multa parece baja.',
  status: 'open',
  author_email: 'reviewer@versiona.test',
  section_key: 'obligaciones-del-contratista',
  section_heading: '3. OBLIGACIONES DEL CONTRATISTA',
  created_on: 1,
  resolved_in: null,
  replies: [],
  anchors: [
    { version_number: 1, page: 1, quads: [{ page: 1, x0: 0, y0: 0, x1: 1, y1: 0.2 }],
      text_snippet: '', method: 'exact' },
    { version_number: 2, page: 1, quads: [{ page: 1, x0: 0, y0: 0.3, x1: 1, y1: 0.5 }],
      text_snippet: '', method: 'reanchored_section' },
  ],
  created_at: '2026-07-12T10:00:00Z',
  ...over,
});

const baseProps = {
  versionId: 'v2',
  versionNumber: 2,
  sections: [{ stable_key: 's1', heading_text: '1. OBJETO', level: 1, order_index: 0,
               page_start: 1, page_end: 1, char_count: 10 }],
  canCreate: true,
  canReply: true,
  currentUserEmail: 'reviewer@versiona.test',
};

describe('ObservationsPanel (D3)', () => {
  beforeEach(() => {
    items = [];
    fetch.mockReset();
    reply.mockReset();
    setStatus.mockReset();
  });

  it('[D3-L01] shows the guided empty state', () => {
    render(<ObservationsPanel {...baseProps} />);

    expect(screen.getByText('Sin observaciones')).toBeInTheDocument();
  });

  it('[D3-F01] renders a thread with its re-anchored badge for THIS version', () => {
    items = [observation()];

    render(<ObservationsPanel {...baseProps} />);

    expect(screen.getByText('Abierta')).toBeInTheDocument();
    expect(screen.getByText(/Re-anclada/)).toBeInTheDocument();
  });

  it('[D3-F01b] selecting the anchor emits the version quads for highlighting', async () => {
    items = [observation()];
    const onSelectAnchor = jest.fn();

    render(<ObservationsPanel {...baseProps} onSelectAnchor={onSelectAnchor} />);
    await userEvent.click(screen.getByTestId('observation-anchor-o1'));

    expect(onSelectAnchor).toHaveBeenCalledWith([
      { page: 1, x0: 0, y0: 0.3, x1: 1, y1: 0.5 },
    ]);
  });

  it('[D3-F02] sends a reply', async () => {
    items = [observation()];
    reply.mockResolvedValue(true);

    render(<ObservationsPanel {...baseProps} />);
    await userEvent.type(screen.getByTestId('reply-input-o1'), 'Lo corregimos.');
    await userEvent.click(screen.getByTestId('reply-send-o1'));

    expect(reply).toHaveBeenCalledWith('v2', 'o1', 'Lo corregimos.');
  });

  it('[D3-F03] resolve appears only when answered and reopen when resolved', () => {
    items = [observation({ status: 'answered' })];
    const { rerender } = render(<ObservationsPanel {...baseProps} />);
    expect(screen.getByTestId('resolve-o1')).toBeInTheDocument();

    items = [observation({ status: 'resolved', resolved_in: 3 })];
    rerender(<ObservationsPanel {...baseProps} versionNumber={2} />);
    expect(screen.queryByTestId('resolve-o1')).not.toBeInTheDocument();
  });

  it('[D3-A01] resolved threads hide behind the toggle', async () => {
    items = [observation({ status: 'resolved' })];

    render(<ObservationsPanel {...baseProps} />);
    expect(screen.queryByTestId('observation-o1')).not.toBeInTheDocument();

    await userEvent.click(screen.getByTestId('show-resolved'));
    expect(screen.getByTestId('observation-o1')).toBeInTheDocument();
    expect(screen.getByTestId('reopen-o1')).toBeInTheDocument();
  });

  it('[D3-P02] hides creation from non-reviewers', () => {
    render(<ObservationsPanel {...baseProps} canCreate={false} />);

    expect(screen.queryByTestId('add-observation')).not.toBeInTheDocument();
  });
});
