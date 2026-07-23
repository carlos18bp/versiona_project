import { render, screen, within } from '@testing-library/react';

import ProjectPage from '../page';
import { api } from '@/lib/services/http';

jest.mock('@/lib/services/http', () => ({ api: { get: jest.fn(), post: jest.fn() } }));
jest.mock('@/lib/hooks/useRequireAuth', () => ({
  useRequireAuth: () => ({ isAuthenticated: true }),
}));
jest.mock('next/navigation', () => ({
  useParams: () => ({ projectId: 'p1' }),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

const mockGet = api.get as jest.Mock;

const RESPONSES: Record<string, unknown> = {
  'projects/p1/documents/': { count: 0, next: null, previous: null, results: [] },
  'projects/p1/saved_comparisons/': { results: [] },
  'projects/p1/activity/': { results: [] },
  'projects/p1/': { name: 'Torre Central', status: 'active', effective_role: 'editor' },
};

describe('ProjectPage screen states (C1)', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockGet.mockImplementation((url: string) =>
      Promise.resolve({ data: RESPONSES[url] })
    );
  });

  it('[C1-L01] shows the guided empty state when the project has no documents', async () => {
    render(<ProjectPage />);

    const empty = await screen.findByTestId('empty-state');
    expect(within(empty).getByText('Este proyecto no tiene documentos')).toBeInTheDocument();
  });

  it('[C1-L01] explains the next step in the empty state description', async () => {
    render(<ProjectPage />);

    const empty = await screen.findByTestId('empty-state');
    expect(
      within(empty).getByText('Arrastra un PDF o haz clic para subir la primera versión.')
    ).toBeInTheDocument();
  });

  it('[C1-L01] keeps the upload dropzone as the protagonist of the empty project', async () => {
    render(<ProjectPage />);

    await screen.findByTestId('empty-state');
    expect(
      within(screen.getByTestId('upload-dropzone')).getByText(
        'Arrastra tu PDF aquí o haz clic para elegirlo'
      )
    ).toBeInTheDocument();
  });

  it('[C1-L01] does not render the documents list when the project is empty', async () => {
    render(<ProjectPage />);

    await screen.findByTestId('empty-state');
    expect(screen.queryByTestId('documents-list')).not.toBeInTheDocument();
  });
});
