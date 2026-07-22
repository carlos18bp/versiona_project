import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { TrialBanner } from '../TrialBanner';
import { api } from '../../../lib/services/http';
import { useTrialStore } from '../../../lib/stores/trialStore';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));
jest.mock('../../../lib/stores/authStore', () => ({
  useAuthStore: (selector: (s: { isAuthenticated: boolean }) => unknown) =>
    selector({ isAuthenticated: true }),
}));
jest.mock('../../../lib/stores/orgStore', () => ({
  useOrgStore: (selector: (s: { activeOrgId: string }) => unknown) =>
    selector({ activeOrgId: 'org-1' }),
}));

const mockGet = api.get as jest.Mock;

function mockTrial(days_left: number | null, on_trial = true) {
  mockGet.mockResolvedValueOnce({
    data: { trial: { on_trial, trial_ends_at: '2026-08-05T13:00:00Z', days_left } },
  });
}

describe('TrialBanner', () => {
  beforeEach(() => {
    mockGet.mockReset();
    sessionStorage.clear();
    useTrialStore.setState({ trial: null, fetchedOrgId: null });
  });

  it('renders the plural day count from the usage trial', async () => {
    mockTrial(12);

    render(<TrialBanner />);

    expect(await screen.findByTestId('trial-banner')).toHaveTextContent(
      'Prueba Pro: quedan 12 días'
    );
  });

  it('renders the singular copy for one day left', async () => {
    mockTrial(1);

    render(<TrialBanner />);

    expect(await screen.findByTestId('trial-banner')).toHaveTextContent(
      'Prueba Pro: queda 1 día'
    );
  });

  it('hides after dismiss and persists the choice in sessionStorage', async () => {
    mockTrial(10);
    render(<TrialBanner />);
    await screen.findByTestId('trial-banner');

    await userEvent.click(screen.getByTestId('trial-banner-dismiss'));

    expect(screen.queryByTestId('trial-banner')).not.toBeInTheDocument();
    expect(sessionStorage.getItem('versiona-trial-banner-dismissed')).toBe('1');
  });

  it('renders nothing when the org is not on trial', async () => {
    mockTrial(null, false);

    render(<TrialBanner />);

    await waitFor(() => expect(mockGet).toHaveBeenCalled());
    expect(screen.queryByTestId('trial-banner')).not.toBeInTheDocument();
  });
});
