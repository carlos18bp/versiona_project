import { render, screen } from '@testing-library/react';

import DocumentTimelinePage from '../page';
import { api } from '@/lib/services/http';

jest.mock('@/lib/services/http', () => ({ api: { get: jest.fn(), post: jest.fn() } }));
jest.mock('@/lib/hooks/useRequireAuth', () => ({
  useRequireAuth: () => ({ isAuthenticated: true }),
}));
jest.mock('next/navigation', () => ({
  useParams: () => ({ projectId: 'p1', docId: 'd1' }),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn() }),
}));

const mockGet = api.get as jest.Mock;

function makeVersion(number: number) {
  return {
    public_id: `v${number}`,
    number,
    message: `cambio ${number}`,
    author_email: 'ana@example.com',
    created_at: '2026-07-12T10:00:00Z',
    is_draft: false,
    is_approved: false,
    is_trashed: false,
    analysis_status: 'ready',
    source_scenario: 'text_native',
    page_count: 4,
    thumb_url: null,
    check_summary: null,
    error_detail: null,
  };
}

const SINGLE_VERSION_PAGE = {
  count: 1,
  next: null,
  previous: null,
  results: [makeVersion(1)],
};

const FIRST_OF_60_VERSIONS = {
  count: 60,
  next: 'documents/d1/versions/?page=2',
  previous: null,
  results: Array.from({ length: 25 }, (_, index) => makeVersion(60 - index)),
};

describe('DocumentTimelinePage screen states (C2/C3)', () => {
  beforeEach(() => mockGet.mockReset());

  it('[C2-L01] disables the compare CTA when the document has a single version', async () => {
    mockGet.mockResolvedValueOnce({ data: SINGLE_VERSION_PAGE });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-1');
    expect(screen.getByTestId('compare-selected')).toBeDisabled();
  });

  it('[C2-L01] explains that two versions are required to compare', async () => {
    mockGet.mockResolvedValueOnce({ data: SINGLE_VERSION_PAGE });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-1');
    expect(screen.getByText('Elige dos versiones para comparar')).toBeInTheDocument();
  });

  it('[C2-L01] offers a single selectable version so two can never be picked', async () => {
    mockGet.mockResolvedValueOnce({ data: SINGLE_VERSION_PAGE });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-1');
    expect(screen.getAllByRole('checkbox')).toHaveLength(1);
  });

  it('[C3-L01] renders the timeline pagination when there are more than 25 versions', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_VERSIONS });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-60');
    expect(screen.getByRole('button', { name: 'Siguiente' })).toBeEnabled();
  });

  it('[C3-L01] starts the paginated timeline on page one with no previous page', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_VERSIONS });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-60');
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled();
  });

  it('[C3-L01] shows the current page indicator of the paginated timeline', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_VERSIONS });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-60');
    expect(screen.getByText('Página 1')).toBeInTheDocument();
  });

  it('[C3-L01] renders only the 25 versions of the first page', async () => {
    mockGet.mockResolvedValueOnce({ data: FIRST_OF_60_VERSIONS });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-60');
    expect(screen.getAllByRole('checkbox')).toHaveLength(25);
  });

  it('[C2-L01] hides the pagination controls for a single-version document', async () => {
    mockGet.mockResolvedValueOnce({ data: SINGLE_VERSION_PAGE });

    render(<DocumentTimelinePage />);

    await screen.findByTestId('version-item-1');
    expect(screen.queryByRole('button', { name: 'Siguiente' })).not.toBeInTheDocument();
  });
});
