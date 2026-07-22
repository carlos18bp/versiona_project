import { act, render, screen, waitFor } from '@testing-library/react';

import StagingGate from '../StagingGate';
import { api } from '../../../lib/services/http';
import type { StagingBannerState } from '../../../lib/services/staging-banner';
import { useLocaleStore } from '../../../lib/stores/localeStore';
import { useStagingBannerStore } from '../../../lib/stores/stagingBannerStore';

jest.mock('../../../lib/services/http', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

const createBannerState = (
  overrides: Partial<StagingBannerState> = {}
): StagingBannerState => ({
  is_visible: true,
  current_phase: 'design',
  phase_labels: { es: 'Fase de diseño', en: 'Design phase' },
  started_at: '2026-07-01T00:00:00Z',
  expires_at: '2026-07-30T00:00:00Z',
  days_remaining: 8,
  is_expired: false,
  contact_whatsapp: '+57 300 123 4567',
  contact_email: 'equipo@projectapp.co',
  ...overrides,
});

const waitForFetch = () =>
  waitFor(() => expect(useStagingBannerStore.getState().hasFetched).toBe(true));

describe('StagingGate', () => {
  beforeEach(() => {
    mockGet.mockReset();
    localStorage.clear();
    useLocaleStore.setState({ locale: 'es' });
    useStagingBannerStore.setState({ state: null, isLoading: false, hasFetched: false });
  });

  afterEach(() => {
    jest.useRealTimers();
    localStorage.clear();
  });

  it('renders the children while the banner state is unknown', () => {
    mockGet.mockReturnValueOnce(new Promise(() => {}));

    render(
      <StagingGate>
        <p data-testid="gate-child">contenido</p>
      </StagingGate>
    );

    expect(screen.getByTestId('gate-child')).toBeInTheDocument();
    expect(screen.queryByTestId('staging-phase-banner')).not.toBeInTheDocument();
  });

  it('renders the children without a banner when it is hidden', async () => {
    mockGet.mockResolvedValue({ data: createBannerState({ is_visible: false }) });

    render(
      <StagingGate>
        <p data-testid="gate-child">contenido</p>
      </StagingGate>
    );
    await waitForFetch();

    expect(screen.getByTestId('gate-child')).toBeInTheDocument();
    expect(screen.queryByTestId('staging-phase-banner')).not.toBeInTheDocument();
  });

  it('renders the children without a banner before the phase starts', async () => {
    mockGet.mockResolvedValue({ data: createBannerState({ started_at: null }) });

    render(
      <StagingGate>
        <p data-testid="gate-child">contenido</p>
      </StagingGate>
    );
    await waitForFetch();

    expect(screen.getByTestId('gate-child')).toBeInTheDocument();
    expect(screen.queryByTestId('staging-phase-banner')).not.toBeInTheDocument();
  });

  it('shows the phase banner above the children during an active phase', async () => {
    mockGet.mockResolvedValue({ data: createBannerState() });

    render(
      <StagingGate>
        <p data-testid="gate-child">contenido</p>
      </StagingGate>
    );

    expect(await screen.findByTestId('staging-phase-banner')).toBeInTheDocument();
    expect(screen.getByTestId('gate-child')).toBeInTheDocument();
  });

  it('replaces the children with the overlay when the phase expired', async () => {
    mockGet.mockResolvedValue({ data: createBannerState({ is_expired: true }) });

    render(
      <StagingGate>
        <p data-testid="gate-child">contenido</p>
      </StagingGate>
    );

    expect(await screen.findByTestId('staging-expired-overlay')).toBeInTheDocument();
    expect(screen.queryByTestId('gate-child')).not.toBeInTheDocument();
  });

  it('polls the banner state every minute', async () => {
    jest.useFakeTimers();
    mockGet.mockResolvedValue({ data: createBannerState({ is_visible: false }) });

    render(
      <StagingGate>
        <p data-testid="gate-child">contenido</p>
      </StagingGate>
    );
    await act(async () => {
      await jest.advanceTimersByTimeAsync(60_000);
    });

    expect(mockGet).toHaveBeenCalledTimes(2);
  });
});
