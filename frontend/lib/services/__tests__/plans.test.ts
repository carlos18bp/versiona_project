import { publicApi } from '../http';
import { fetchPublicPlans, formatCop, STATIC_PLANS } from '../plans';

jest.mock('../http', () => ({
  publicApi: { get: jest.fn() },
}));

const mockGet = publicApi.get as jest.Mock;

describe('plans service', () => {
  beforeEach(() => mockGet.mockReset());

  it('formats COP thousands with dots and no decimals', () => {
    expect(formatCop(149000)).toMatch(/149\.000/);
  });

  it('maps the API payload into plans and trial days', async () => {
    mockGet.mockResolvedValueOnce({
      data: { trial_days: 14, plans: STATIC_PLANS },
    });

    const result = await fetchPublicPlans();

    expect(result.fromFallback).toBe(false);
    expect(result.trialDays).toBe(14);
    expect(result.plans[1].limits.max_members).toBe(25);
  });

  it('falls back to the static catalog on network failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('down'));

    const result = await fetchPublicPlans();

    expect(result.fromFallback).toBe(true);
    expect(result.plans).toEqual(STATIC_PLANS);
  });
});
