import { render, screen } from '@testing-library/react';

import { SavedComparisons } from '../SavedComparisons';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));

const mockGet = api.get as jest.Mock;

describe('SavedComparisons (E2)', () => {
  beforeEach(() => mockGet.mockReset());

  it('[E2-F01-ui] lists saved comparisons with their direct link', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        results: [{
          public_id: 's1',
          name: 'Entrega 1 vs 2',
          created_by: 'editor@x.co',
          document_title: 'Contrato',
          summary: '2 modificadas, 1 eliminada, 1 agregada',
          link: '/projects/p1/documents/d1/compare/v1/v2',
        }],
      },
    });

    render(<SavedComparisons projectId="p1" />);

    const row = await screen.findByTestId('saved-Entrega 1 vs 2');
    expect(row).toHaveAttribute('href', '/projects/p1/documents/d1/compare/v1/v2');
    expect(screen.getByText(/2 modificadas/)).toBeInTheDocument();
  });

  it('[E2-L01] renders nothing when the project has none', async () => {
    mockGet.mockResolvedValueOnce({ data: { results: [] } });

    const { container } = render(<SavedComparisons projectId="p1" />);

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(container.querySelector('[data-testid="saved-comparisons"]')).toBeNull();
  });
});
