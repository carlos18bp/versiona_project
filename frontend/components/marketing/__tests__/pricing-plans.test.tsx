import { render, screen } from '@testing-library/react';

import { PricingPlans } from '../PricingPlans';
import { publicApi } from '../../../lib/services/http';
import { STATIC_PLANS } from '../../../lib/services/plans';

jest.mock('../../../lib/services/http', () => ({
  publicApi: { get: jest.fn() },
}));

const mockGet = publicApi.get as jest.Mock;

describe('PricingPlans', () => {
  beforeEach(() => mockGet.mockReset());

  it('renders the three plan cards from the API', async () => {
    mockGet.mockResolvedValueOnce({ data: { trial_days: 14, plans: STATIC_PLANS } });

    render(<PricingPlans />);

    expect(await screen.findByTestId('plan-card-free')).toBeInTheDocument();
    expect(screen.getByTestId('plan-card-pro')).toBeInTheDocument();
    expect(screen.getByTestId('plan-card-enterprise')).toBeInTheDocument();
    expect(screen.queryByTestId('pricing-fallback')).not.toBeInTheDocument();
  });

  it('marks Pro as recommended with the trial badge and COP price', async () => {
    mockGet.mockResolvedValueOnce({ data: { trial_days: 14, plans: STATIC_PLANS } });

    render(<PricingPlans />);

    const pro = await screen.findByTestId('plan-card-pro');
    expect(pro).toHaveTextContent('Recomendado');
    expect(pro).toHaveTextContent('14 días gratis al registrarte');
    expect(pro).toHaveTextContent(/149\.000/);
  });

  it('[PR-E01] renders the static fallback marker when the API fails', async () => {
    mockGet.mockRejectedValueOnce(new Error('down'));

    render(<PricingPlans />);

    expect(await screen.findByTestId('pricing-fallback')).toBeInTheDocument();
    expect(screen.getByTestId('plan-card-free')).toBeInTheDocument();
  });
});
