import { render, screen } from '@testing-library/react';

import ProjectsBoardPage from '../page';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));
jest.mock('../../../lib/hooks/useRequireAuth', () => ({
  useRequireAuth: () => ({ isAuthenticated: true }),
}));
jest.mock('../../../lib/stores/orgStore', () => {
  const state = { activeOrgId: 'org-1', fetchOrgs: jest.fn() };
  return { useOrgStore: (selector: (s: typeof state) => unknown) => selector(state) };
});

const mockGet = api.get as jest.Mock;

const project = {
  public_id: 'p1',
  name: 'Torre Central',
  slug: 'torre',
  description: 'Expediente',
  status: 'active',
  is_sample: false,
  document_count: 2,
  effective_role: 'editor',
  created_at: '2026-07-12T00:00:00Z',
  updated_at: '2026-07-12T00:00:00Z',
};

describe('ProjectsBoardPage', () => {
  beforeEach(() => mockGet.mockReset());

  it('[B2-F01] renders project cards with state badge and role', async () => {
    mockGet.mockResolvedValueOnce({
      data: { count: 1, next: null, previous: null, results: [project] },
    });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Torre Central')).toBeInTheDocument();
    expect(screen.getByText('Activo')).toBeInTheDocument();
    expect(screen.getByText(/Editor/)).toBeInTheDocument();
  });

  it('[B2-L01] shows the guided empty state with the create CTA', async () => {
    mockGet.mockResolvedValueOnce({
      data: { count: 0, next: null, previous: null, results: [] },
    });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Aún no tienes proyectos')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Crear proyecto' })).toHaveAttribute(
      'href',
      '/projects/new'
    );
  });

  it('[Board-E] shows the error state with a retry button', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { error: 'Fallo de red' } } });

    render(<ProjectsBoardPage />);

    expect(await screen.findByTestId('async-error')).toHaveTextContent('Fallo de red');
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
  });
});
