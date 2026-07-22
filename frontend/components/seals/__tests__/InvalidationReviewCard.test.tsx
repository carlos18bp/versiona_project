import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { InvalidationReviewCard } from '../InvalidationReviewCard';
import type { ValidityRecord } from '../../../lib/stores/sealStore';

const confirmPlan = jest.fn();

jest.mock('../../../lib/stores/sealStore', () => ({
  useSealStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ confirmPlan, isSubmitting: false, error: null }),
    { getState: () => ({ error: null }) }
  ),
}));

const pending: ValidityRecord[] = [
  {
    seal: {
      public_id: 's-b',
      reviewer_email: 'b@versiona.test',
      version_number: 1,
      covers_all: false,
      covered_keys: ['obligaciones-del-contratista'],
      key_id: 'k1',
      is_active: true,
      revoked_at: null,
      created_at: '2026-07-12T10:00:00Z',
    },
    to_version: 2,
    decision: 'pending_confirmation',
    proposed_decision: 'invalidated',
    reason_code: 'section_modified',
    evidence: {
      changed: [{ stable_key: 'obligaciones-del-contratista', change_type: 'modified' }],
    },
    decided_mode: 'coordinator',
    decided_by_email: null,
    decided_at: null,
  },
];

describe('InvalidationReviewCard', () => {
  beforeEach(() => confirmPlan.mockReset());

  it('[D5-A04] preselects the engine proposal per seal', () => {
    render(<InvalidationReviewCard versionId="v2" pending={pending} />);

    expect(screen.getByTestId('plan-invalidated-s-b')).toBeChecked();
    expect(screen.getByTestId('plan-preserved-s-b')).not.toBeChecked();
    expect(screen.getByText(/Propuesta del motor/)).toBeInTheDocument();
  });

  it('[D5-A06] the coordinator can flip to preserve and confirm', async () => {
    confirmPlan.mockResolvedValue(true);
    render(<InvalidationReviewCard versionId="v2" pending={pending} />);

    await userEvent.click(screen.getByTestId('plan-preserved-s-b'));
    await userEvent.click(screen.getByTestId('confirm-plan'));

    expect(confirmPlan).toHaveBeenCalledWith('v2', { 's-b': 'preserved' });
  });

  it('shows the evidence of what changed', () => {
    render(<InvalidationReviewCard versionId="v2" pending={pending} />);

    expect(screen.getByText(/obligaciones-del-contratista/)).toBeInTheDocument();
  });
});
