import { render, screen } from '@testing-library/react';

import { ChecksPanel } from '../ChecksPanel';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));

const mockGet = api.get as jest.Mock;

describe('ChecksPanel (E3)', () => {
  beforeEach(() => mockGet.mockReset());

  it('[E3-L01] tells when the version has no configured checks', async () => {
    mockGet.mockResolvedValueOnce({
      data: { summary: null, config_version: 1, results: [] },
    });

    render(<ChecksPanel versionId="v1" />);

    expect(
      await screen.findByText('Esta versión no tiene checks configurados')
    ).toBeInTheDocument();
  });

  it('[E3-F02] renders outcomes with their evidence location', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        summary: { pass: 1, warn: 1, fail: 0 },
        config_version: 2,
        results: [
          {
            key: 'tiene-anticipo',
            label: 'Regula el anticipo',
            outcome: 'pass',
            evidence: { section: 'valor-y-forma-de-pago', page: 1, snippet: 'un anticipo del' },
            message: '',
          },
          {
            key: 'tiene-poliza',
            label: 'Póliza de cumplimiento',
            outcome: 'warn',
            evidence: { reason: 'text_missing' },
            message: 'El texto requerido no aparece en el documento.',
          },
        ],
      },
    });

    render(<ChecksPanel versionId="v1" />);

    expect(await screen.findByTestId('checks-summary')).toHaveTextContent('✓ 1');
    const anticipo = screen.getByTestId('check-tiene-anticipo');
    expect(anticipo).toHaveAttribute('data-outcome', 'pass');
    expect(anticipo).toHaveTextContent('valor-y-forma-de-pago');
    expect(anticipo).toHaveTextContent('un anticipo del');
    expect(screen.getByTestId('check-tiene-poliza')).toHaveTextContent(
      'El texto requerido no aparece'
    );
    expect(screen.getByText('Config v2')).toBeInTheDocument();
  });

  it('renders nothing while loading or on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('500'));

    render(<ChecksPanel versionId="v1" />);

    expect(screen.queryByTestId('checks-panel')).not.toBeInTheDocument();
  });
});
