import { api } from '../../services/http';
import type { StagingBannerState } from '../../services/staging-banner';
import { useStagingBannerStore } from '../stagingBannerStore';

jest.mock('../../services/http', () => ({
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

describe('stagingBannerStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    useStagingBannerStore.setState({ state: null, isLoading: false, hasFetched: false });
  });

  it('stores the fetched banner state', async () => {
    const banner = createBannerState();
    mockGet.mockResolvedValueOnce({ data: banner });

    await useStagingBannerStore.getState().fetch();

    expect(useStagingBannerStore.getState().state).toEqual(banner);
    expect(useStagingBannerStore.getState().isLoading).toBe(false);
  });

  it('marks hasFetched after a successful fetch', async () => {
    mockGet.mockResolvedValueOnce({ data: createBannerState() });

    await useStagingBannerStore.getState().fetch();

    expect(useStagingBannerStore.getState().hasFetched).toBe(true);
  });

  it('marks hasFetched even when the fetch fails', async () => {
    mockGet.mockRejectedValueOnce(new Error('down'));

    await useStagingBannerStore.getState().fetch();

    expect(useStagingBannerStore.getState()).toMatchObject({
      state: null,
      isLoading: false,
      hasFetched: true,
    });
  });

  it('keeps the same state reference when the payload is unchanged', async () => {
    mockGet.mockResolvedValueOnce({ data: createBannerState() });
    await useStagingBannerStore.getState().fetch();
    const first = useStagingBannerStore.getState().state;
    mockGet.mockResolvedValueOnce({ data: createBannerState() });

    await useStagingBannerStore.getState().fetch();

    expect(useStagingBannerStore.getState().state).toBe(first);
  });

  it('replaces the state when the payload changes', async () => {
    mockGet.mockResolvedValueOnce({ data: createBannerState() });
    await useStagingBannerStore.getState().fetch();
    mockGet.mockResolvedValueOnce({ data: createBannerState({ days_remaining: 2 }) });

    await useStagingBannerStore.getState().fetch();

    expect(useStagingBannerStore.getState().state?.days_remaining).toBe(2);
  });
});
