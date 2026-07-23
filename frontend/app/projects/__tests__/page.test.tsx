import { render, screen, within } from '@testing-library/react';

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

function makeProject(index: number) {
  return { ...project, public_id: `p${index}`, name: `Proyecto ${index}` };
}

const FIRST_OF_60_PROJECTS = {
  count: 60,
  next: 'orgs/org-1/projects/?page=2',
  previous: null,
  results: Array.from({ length: 25 }, (_, index) => makeProject(index + 1)),
};

describe('ProjectsBoardPage', () => {
  beforeEach(() => mockGet.mockReset());

  it('[B2-F01] renders project cards with state badge and role', async () => {
    mockGet.mockResolvedValueOnce({
      data: { count: 1, next: null, previous: null, results: [project] },
    });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Torre Central')).toBeInTheDocument();
    expect(
      within(screen.getByTestId('projects-grid')).getByText('Activo')
    ).toBeInTheDocument();
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

  it('[B2-L02] enables the next-page control when the board holds more than 25 projects', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_PROJECTS });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Proyecto 1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeEnabled();
  });

  it('[B2-L02] disables the previous-page control on the first page of the board', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_PROJECTS });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Proyecto 1')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled();
  });

  it('[B2-L02] shows the current page indicator of the paginated board', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_PROJECTS });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Proyecto 1')).toBeInTheDocument();
    expect(screen.getByText('Página 1')).toBeInTheDocument();
  });

  it('[B2-L02] renders only the 25 projects of the first page', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_PROJECTS });

    render(<ProjectsBoardPage />);

    expect(await screen.findByText('Proyecto 1')).toBeInTheDocument();
    expect(within(screen.getByTestId('projects-grid')).getAllByRole('listitem')).toHaveLength(25);
  });

  it('[Board-E] shows the error state with a retry button', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { error: 'Fallo de red' } } });

    render(<ProjectsBoardPage />);

    expect(await screen.findByTestId('async-error')).toHaveTextContent('Fallo de red');
    expect(screen.getByRole('button', { name: 'Reintentar' })).toBeInTheDocument();
  });
});
