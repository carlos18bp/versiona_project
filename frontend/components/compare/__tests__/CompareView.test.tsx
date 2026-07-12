import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { CompareView } from '../CompareView';
import type { ComparisonDetail } from '../../../lib/stores/compareStore';

jest.mock('next/dynamic', () => ({
  __esModule: true,
  default: () => {
    const Stub = () => <div data-testid="pdf-stub" />;
    return Stub;
  },
}));

const compare = jest.fn();
const fetchSectionDiff = jest.fn();
const setActiveSection = jest.fn();
let storeState: Record<string, unknown> = {};

jest.mock('../../../lib/stores/compareStore', () => ({
  useCompareStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) => selector(storeState),
    { getState: () => storeState }
  ),
}));
jest.mock('../../../lib/stores/versionStore', () => ({
  useVersionStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ fetchFileUrl: jest.fn().mockResolvedValue('http://minio/f.pdf') }),
}));
jest.mock('../../../lib/services/http', () => ({
  api: { post: jest.fn().mockResolvedValue({ data: {} }) },
}));
const toast = jest.fn();
jest.mock('../../../components/ui/toast', () => ({
  useToast: () => ({ toast }),
}));

const comparison: ComparisonDetail = {
  public_id: 'cmp1',
  status: 'done',
  summary: { text: '2 modificadas, 1 eliminada, 1 agregada', counts: {} },
  has_changes: true,
  from_version: 'v1',
  to_version: 'v2',
  from_number: 1,
  to_number: 2,
  section_changes: [
    { stable_key: 'objeto', heading_from: '1. OBJETO', heading_to: '1. OBJETO',
      change_type: 'unchanged', similarity: 1, order_index: 0 },
    { stable_key: 'multas', heading_from: '3. MULTAS', heading_to: '3. MULTAS',
      change_type: 'modified', similarity: 0.9, order_index: 1 },
  ],
};

function setState(over: Record<string, unknown> = {}) {
  storeState = {
    comparison,
    diffs: {},
    activeSection: null,
    isLoading: false,
    error: null,
    compare,
    fetchSectionDiff,
    setActiveSection,
    ...over,
  };
}

const baseProps = {
  documentId: 'd1',
  fromVersionId: 'v1',
  toVersionId: 'v2',
  view: 'side' as const,
  onViewChange: jest.fn(),
};

describe('CompareView (E1)', () => {
  beforeEach(() => {
    compare.mockReset();
    fetchSectionDiff.mockResolvedValue(null);
    setState();
  });

  it('[E1-F01] the side-by-side view renders both viewers and the summary', async () => {
    render(<CompareView {...baseProps} />);

    expect(compare).toHaveBeenCalledWith('d1', 'v1', 'v2');
    expect(screen.getByTestId('side-before')).toBeInTheDocument();
    expect(screen.getByTestId('side-after')).toBeInTheDocument();
    expect(screen.getByText(/2 modificadas, 1 eliminada, 1 agregada/)).toBeInTheDocument();
  });

  it('[E1-F01b] the summary view shows the exact counters', () => {
    render(<CompareView {...baseProps} view="summary" />);

    expect(screen.getByTestId('count-modified')).toHaveTextContent('1');
    expect(screen.getByTestId('count-unchanged')).toHaveTextContent('1');
  });

  it('[E1-F02] next-change selects the first changed section', async () => {
    render(<CompareView {...baseProps} />);

    await userEvent.click(screen.getByTestId('next-change'));

    expect(setActiveSection).toHaveBeenCalledWith('multas');
    expect(fetchSectionDiff).toHaveBeenCalledWith('multas');
  });

  it('[E1-L01] a comparison without changes shows the explicit empty state', () => {
    setState({
      comparison: { ...comparison, has_changes: false, section_changes: [] },
    });

    render(<CompareView {...baseProps} />);

    expect(screen.getByTestId('no-changes')).toBeInTheDocument();
    expect(screen.getByText('Sin cambios entre estas versiones')).toBeInTheDocument();
  });

  it('[E1-E01] a failed comparison offers retry', async () => {
    setState({ comparison: null, error: 'La versión v2 aún no está analizada' });

    render(<CompareView {...baseProps} />);

    expect(screen.getByTestId('async-error')).toHaveTextContent('no está analizada');
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }));
    expect(compare).toHaveBeenCalledTimes(2);
  });

  it('[E2-F01-ui] the save button posts the chosen name', async () => {
    const { api } = jest.requireMock('../../../lib/services/http');
    window.prompt = jest.fn().mockReturnValue('Entrega 1 vs 2');

    render(<CompareView {...baseProps} />);
    await userEvent.click(screen.getByTestId('save-comparison'));

    expect(api.post).toHaveBeenCalledWith('comparisons/cmp1/save/', {
      name: 'Entrega 1 vs 2',
    });
  });
});
