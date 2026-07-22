import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ReviewContextBar } from '../ReviewContextBar';
import type { ReviewContext } from '../../../lib/stores/reviewStore';

const fetchContext = jest.fn();
let contextValue: ReviewContext | null = null;

jest.mock('../../../lib/stores/reviewStore', () => ({
  useReviewStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ context: contextValue, fetchContext }),
}));

describe('ReviewContextBar (D2)', () => {
  beforeEach(() => {
    fetchContext.mockReset();
    contextValue = null;
  });

  it('[D2-L01] renders nothing without a previous seal', () => {
    contextValue = { my_last_sealed_version: null, changed: [], unchanged: [] };

    render(<ReviewContextBar versionId="v2" />);

    expect(screen.queryByTestId('review-context-bar')).not.toBeInTheDocument();
  });

  it('[D2-F01] lists the sections changed since my seal with jump buttons', async () => {
    contextValue = {
      my_last_sealed_version: 1,
      changed: [{ stable_key: 'obligaciones-del-contratista', heading: '3. OBLIGACIONES' }],
      unchanged: [
        { stable_key: 'objeto-del-contrato', heading: '1. OBJETO' },
        { stable_key: 'definiciones', heading: '2. DEFINICIONES' },
      ],
    };
    const onJump = jest.fn();

    render(<ReviewContextBar versionId="v2" onJumpToSection={onJump} />);

    expect(screen.getByText('Ya revisado por ti')).toBeInTheDocument();
    expect(screen.getByText(/Sellaste la v1/)).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // unchanged count badge

    await userEvent.click(
      screen.getByTestId('context-changed-obligaciones-del-contratista')
    );
    expect(onJump).toHaveBeenCalledWith('obligaciones-del-contratista');
  });
});
