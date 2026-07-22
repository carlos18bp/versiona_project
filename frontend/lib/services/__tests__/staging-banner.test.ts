import { api } from '../http';
import { fetchStagingBannerState, type StagingBannerState } from '../staging-banner';

jest.mock('../http', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

const createBannerState = (): StagingBannerState => ({
  is_visible: true,
  current_phase: 'design',
  phase_labels: { es: 'Fase de diseño', en: 'Design phase' },
  started_at: '2026-07-01T00:00:00Z',
  expires_at: '2026-07-30T00:00:00Z',
  days_remaining: 8,
  is_expired: false,
  contact_whatsapp: '+57 300 123 4567',
  contact_email: 'equipo@projectapp.co',
});

describe('fetchStagingBannerState', () => {
  beforeEach(() => {
    mockGet.mockReset();
  });

  it('requests the staging-banner endpoint', async () => {
    mockGet.mockResolvedValueOnce({ data: createBannerState() });

    await fetchStagingBannerState();

    expect(mockGet).toHaveBeenCalledWith('staging-banner/');
  });

  it('returns the banner state payload', async () => {
    const state = createBannerState();
    mockGet.mockResolvedValueOnce({ data: state });

    const result = await fetchStagingBannerState();

    expect(result).toEqual(state);
  });

  it('propagates a failed request', async () => {
    const failure = new Error('boom');
    mockGet.mockRejectedValueOnce(failure);

    await expect(fetchStagingBannerState()).rejects.toBe(failure);
  });
});
