import { render, screen } from '@testing-library/react';

import Header from '../Header';

jest.mock('../../../lib/stores/authStore', () => ({
  useAuthStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ isAuthenticated: true, signOut: jest.fn() }),
}));

const orgsState: { orgs: Array<{ role: string }>; fetchOrgs: jest.Mock } = {
  orgs: [],
  fetchOrgs: jest.fn(),
};

jest.mock('../../../lib/stores/orgStore', () => ({
  useOrgStore: (selector: (s: typeof orgsState) => unknown) => selector(orgsState),
}));

describe('Header role-based navigation', () => {
  it('[Header-R1] hides the trash link for a plain org member', () => {
    orgsState.orgs = [{ role: 'member' }];

    render(<Header />);

    expect(screen.queryByRole('link', { name: 'Papelera' })).not.toBeInTheDocument();
  });

  it('[Header-R2] shows the trash link for an org admin', () => {
    orgsState.orgs = [{ role: 'admin' }];

    render(<Header />);

    expect(screen.getByRole('link', { name: 'Papelera' })).toHaveAttribute('href', '/org/trash');
  });

  it('[Header-R3] shows the trash link for the org owner', () => {
    orgsState.orgs = [{ role: 'owner' }];

    render(<Header />);

    expect(screen.getByRole('link', { name: 'Papelera' })).toBeInTheDocument();
  });
});
