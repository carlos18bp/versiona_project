import { render, screen } from '@testing-library/react';

import OrgUsagePage from '../usage/page';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));
jest.mock('../../../lib/hooks/useRequireAuth', () => ({
  useRequireAuth: () => ({ isAuthenticated: true }),
}));
jest.mock('../../../lib/stores/orgStore', () => {
  const state = { activeOrgId: 'org-1', fetchOrgs: jest.fn(), orgs: [] };
  return { useOrgStore: (selector: (s: typeof state) => unknown) => selector(state) };
});

const mockGet = api.get as jest.Mock;

describe('OrgUsagePage (F2)', () => {
  beforeEach(() => mockGet.mockReset());

  it('[F2-F01] shows meters, capacity warnings and the informative CTA', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        plan: 'free',
        plan_label: 'Gratis',
        limits: { max_active_projects: 1, max_members: 2, history_days: 30 },
        usage: { active_projects: 1, members: 2 },
        warnings: [
          { limit: 'max_active_projects', used: 1, max: 1, at_capacity: true },
          { limit: 'max_members', used: 2, max: 2, at_capacity: true },
        ],
        upgrade_available: true,
      },
    });

    render(<OrgUsagePage />);

    expect(await screen.findByTestId('usage-panel')).toBeInTheDocument();
    expect(screen.getByText('1 / 1')).toBeInTheDocument();
    expect(screen.getByText('2 / 2')).toBeInTheDocument();
    expect(screen.getAllByText('Límite alcanzado')).toHaveLength(2);
    expect(screen.getByText(/30 días/)).toBeInTheDocument();
    expect(screen.getByTestId('upgrade-plans-link')).toHaveAttribute('href', '/precios');
    expect(screen.getByTestId('upgrade-contact')).toBeInTheDocument();
  });

  it('[F2-F03] renders the trial line when the org is on trial', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        plan: 'pro',
        plan_label: 'Pro',
        limits: { max_active_projects: 20, max_members: 25, history_days: null },
        usage: { active_projects: 1, members: 1 },
        warnings: [],
        upgrade_available: true,
        effective_plan: 'pro',
        trial: { on_trial: true, trial_ends_at: '2026-08-05T13:00:00Z', days_left: 12 },
      },
    });

    render(<OrgUsagePage />);

    expect(await screen.findByTestId('usage-trial-line')).toHaveTextContent('12');
  });

  it('[F2-F02] pro plan hides the upgrade CTA', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        plan: 'pro',
        plan_label: 'Pro',
        limits: { max_active_projects: 20, max_members: 25, history_days: null },
        usage: { active_projects: 3, members: 7 },
        warnings: [],
        upgrade_available: false,
      },
    });

    render(<OrgUsagePage />);

    expect(await screen.findByTestId('usage-panel')).toBeInTheDocument();
    expect(screen.getByText(/Ilimitado/)).toBeInTheDocument();
    expect(screen.queryByTestId('upgrade-cta')).not.toBeInTheDocument();
  });
});
