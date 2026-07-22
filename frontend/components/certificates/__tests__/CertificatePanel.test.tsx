import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { CertificatePanel } from '../CertificatePanel';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

const toast = jest.fn();
jest.mock('../../../components/ui/toast', () => ({
  useToast: () => ({ toast }),
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

describe('CertificatePanel (E4)', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    window.open = jest.fn();
  });

  it('[E4-L01] renders nothing for an unapproved version without certificates', async () => {
    mockGet.mockResolvedValueOnce({ data: { results: [] } });

    const { container } = render(
      <CertificatePanel versionId="v1" isApproved={false} canIssue={false} />
    );

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(container.querySelector('[data-testid="certificate-panel"]')).toBeNull();
  });

  it('[E4-F01-ui] admin issues and the PDF opens', async () => {
    mockGet.mockResolvedValue({ data: { results: [] } });
    mockPost.mockResolvedValueOnce({
      data: { serial: 'ACME-2026-0001', download_url: 'http://minio/cert.pdf?sig=1' },
    });

    render(<CertificatePanel versionId="v1" isApproved canIssue />);
    await userEvent.click(await screen.findByTestId('issue-certificate'));

    expect(mockPost).toHaveBeenCalledWith('versions/v1/certificates/');
    expect(window.open).toHaveBeenCalledWith(
      'http://minio/cert.pdf?sig=1', '_blank', 'noopener'
    );
  });

  it('[E4-E01-ui] surfaces the domain rejection', async () => {
    mockGet.mockResolvedValue({ data: { results: [] } });
    mockPost.mockRejectedValueOnce({
      response: { data: { error: 'La constancia solo se emite sobre una versión APROBADA.' } },
    });

    render(<CertificatePanel versionId="v1" isApproved canIssue />);
    await userEvent.click(await screen.findByTestId('issue-certificate'));

    expect(toast).toHaveBeenCalledWith(expect.stringContaining('APROBADA'), 'error');
    expect(window.open).not.toHaveBeenCalled();
  });

  it('[E4-P02] hides issuing from non-admins but lists existing certificates', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        results: [{ public_id: 'c1', serial: 'ACME-2026-0001',
                    issued_by: 'admin@x.co', created_at: '2026-07-12', seals: 2 }],
      },
    });

    render(<CertificatePanel versionId="v1" isApproved canIssue={false} />);

    expect(await screen.findByTestId('certificate-ACME-2026-0001')).toBeInTheDocument();
    expect(screen.queryByTestId('issue-certificate')).not.toBeInTheDocument();
    expect(screen.getByText(/2 sellos certificados/)).toBeInTheDocument();
  });
});
