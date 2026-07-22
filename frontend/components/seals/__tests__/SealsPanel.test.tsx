import { render, screen } from '@testing-library/react';

import { SealsPanel } from '../SealsPanel';
import type { SealSummary, ValidityRecord } from '../../../lib/stores/sealStore';

const fetchSeals = jest.fn();
const fetchPlan = jest.fn();
const verifySeal = jest.fn();
const confirmPlan = jest.fn();

let storeState: Record<string, unknown> = {};

jest.mock('../../../lib/stores/sealStore', () => ({
  useSealStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) => selector(storeState),
    { getState: () => storeState }
  ),
}));

const seal: SealSummary = {
  public_id: 's1',
  reviewer_email: 'a@versiona.test',
  version_number: 1,
  covers_all: false,
  covered_keys: ['objeto-del-contrato', 'definiciones'],
  key_id: 'k1',
  is_active: true,
  revoked_at: null,
  created_at: '2026-07-12T10:00:00Z',
};

const record = (over: Partial<ValidityRecord> = {}): ValidityRecord => ({
  seal,
  to_version: 2,
  decision: 'preserved',
  proposed_decision: 'preserved',
  reason_code: 'all_sections_unchanged',
  evidence: { verified: [{ stable_key: 'objeto-del-contrato' }] },
  decided_mode: 'auto',
  decided_by_email: null,
  decided_at: '2026-07-12T11:00:00Z',
  ...over,
});

function setState(over: Record<string, unknown> = {}) {
  storeState = {
    seals: [],
    validityRecords: [],
    pendingPlan: [],
    isLoading: false,
    isSubmitting: false,
    error: null,
    fetchSeals,
    fetchPlan,
    verifySeal,
    confirmPlan,
    ...over,
  };
}

describe('SealsPanel', () => {
  beforeEach(() => {
    fetchSeals.mockReset();
    fetchPlan.mockReset();
    setState();
  });

  it('[D4-L01] shows the guided empty state without seals', () => {
    render(<SealsPanel versionId="v1" canConfirmPlan={false} />);

    expect(screen.getByText('Esta versión aún no tiene sellos.')).toBeInTheDocument();
  });

  it('[D4-F01] lists a seal with its scope and validity badge', () => {
    setState({ seals: [seal] });

    render(<SealsPanel versionId="v1" canConfirmPlan={false} />);

    expect(screen.getByTestId('seal-a@versiona.test')).toBeInTheDocument();
    expect(screen.getByText('Vigente')).toBeInTheDocument();
    expect(screen.getByText(/objeto-del-contrato, definiciones/)).toBeInTheDocument();
  });

  it('[D5-F02] renders a preserved record with its hash-equality reason', () => {
    setState({ validityRecords: [record()] });

    render(<SealsPanel versionId="v2" canConfirmPlan={false} />);

    const card = screen.getByTestId('validity-a@versiona.test');
    expect(card).toHaveAttribute('data-decision', 'preserved');
    expect(screen.getByText('Conservado')).toBeInTheDocument();
    expect(screen.getByText(/igualdad de hash verificada/)).toBeInTheDocument();
  });

  it('[D5-F01] renders an invalidated record with the changed sections', () => {
    setState({
      validityRecords: [
        record({
          decision: 'invalidated',
          reason_code: 'section_modified',
          evidence: {
            changed: [{ stable_key: 'obligaciones-del-contratista', change_type: 'modified' }],
            still_intact: [{ stable_key: 'objeto-del-contrato' }],
          },
        }),
      ],
    });

    render(<SealsPanel versionId="v2" canConfirmPlan={false} />);

    expect(screen.getByText('Requiere re-revisión')).toBeInTheDocument();
    expect(screen.getByText(/obligaciones-del-contratista/)).toBeInTheDocument();
    expect(screen.getByText(/Secciones intactas del sello/)).toBeInTheDocument();
  });

  it('[D5-A04] shows the coordinator card only to who can confirm', () => {
    setState({
      pendingPlan: [record({ decision: 'pending_confirmation', proposed_decision: 'invalidated' })],
    });

    const { rerender } = render(<SealsPanel versionId="v2" canConfirmPlan={false} />);
    expect(screen.queryByTestId('invalidation-review-card')).not.toBeInTheDocument();

    rerender(<SealsPanel versionId="v2" canConfirmPlan />);
    expect(screen.getByTestId('invalidation-review-card')).toBeInTheDocument();
  });

  it('[D4-A01] offers withdrawal only on my own active seal', () => {
    setState({ seals: [seal] });
    const onWithdraw = jest.fn();

    const { rerender } = render(
      <SealsPanel
        versionId="v1"
        canConfirmPlan={false}
        currentUserEmail="otra@versiona.test"
        onWithdraw={onWithdraw}
      />
    );
    expect(screen.queryByTestId('withdraw-seal')).not.toBeInTheDocument();

    rerender(
      <SealsPanel
        versionId="v1"
        canConfirmPlan={false}
        currentUserEmail="a@versiona.test"
        onWithdraw={onWithdraw}
      />
    );
    expect(screen.getByTestId('withdraw-seal')).toBeInTheDocument();
  });
});
