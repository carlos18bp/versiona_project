import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { UploadDropzone } from '../UploadDropzone';

jest.mock('next/dynamic', () => ({
  __esModule: true,
  default: () => {
    const Stub = () => <div data-testid="local-pdf-preview" />;
    return Stub;
  },
}));

const uploadVersion = jest.fn();
const createDocument = jest.fn();
const resetUpload = jest.fn();
let uploadState: Record<string, unknown> = {
  phase: 'idle', progress: 0, error: null, jobId: null, version: null,
};

jest.mock('../../../lib/stores/documentStore', () => ({
  useDocumentStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({
      upload: uploadState,
      uploadVersion,
      createDocument,
      resetUpload,
    }),
}));
jest.mock('../../../lib/stores/jobStore', () => ({
  useJobStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ track: jest.fn() }),
}));

describe('UploadDropzone', () => {
  beforeEach(() => {
    uploadVersion.mockReset();
    createDocument.mockReset();
    uploadState = { phase: 'idle', progress: 0, error: null, jobId: null, version: null };
  });

  it('[C1-E02-ui] rejects a non-PDF file before any network call', async () => {
    render(<UploadDropzone documentId="doc-1" />);

    const input = screen.getByTestId('upload-input') as HTMLInputElement;
    await userEvent.upload(input, new File(['x'], 'foto.png', { type: 'image/png' }), {
      applyAccept: false,
    });

    expect(screen.getByTestId('upload-local-error')).toHaveTextContent('PDF');
    expect(uploadVersion).not.toHaveBeenCalled();
  });

  it('[C1-A01] shows the local preview and cancels without spending network', async () => {
    render(<UploadDropzone documentId="doc-1" />);

    const pdf = new File(['%PDF-'], 'contrato.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByTestId('upload-input'), pdf);

    expect(await screen.findByTestId('local-pdf-preview')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }));

    expect(uploadVersion).not.toHaveBeenCalled();
    expect(screen.queryByTestId('local-pdf-preview')).not.toBeInTheDocument();
  });

  it('[C1-F01-ui] confirms the upload with document title and message', async () => {
    uploadVersion.mockResolvedValue({ phase: 'analyzing', jobId: 'j1' });
    createDocument.mockResolvedValue({ public_id: 'doc-9' });
    render(<UploadDropzone projectId="proj-1" />);

    const pdf = new File(['%PDF-'], 'contrato.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByTestId('upload-input'), pdf);
    await userEvent.type(screen.getByTestId('upload-message'), 'primera entrega');
    await userEvent.click(screen.getByTestId('upload-confirm'));

    expect(createDocument).toHaveBeenCalledWith('proj-1', 'contrato');
    expect(uploadVersion).toHaveBeenCalledWith('doc-9', pdf, 'primera entrega');
  });

  it('[C2-F01-ui] shows the analyzing phase after completing', async () => {
    uploadState = { phase: 'analyzing', progress: 100, error: null, jobId: 'j1', version: null };
    render(<UploadDropzone documentId="doc-1" />);
    const pdf = new File(['%PDF-'], 'contrato.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByTestId('upload-input'), pdf);

    expect(screen.getByTestId('upload-analyzing')).toBeInTheDocument();
    expect(screen.getByTestId('upload-confirm')).toBeDisabled();
  });

  it('[C1-E04-ui] surfaces the backend error with the failed phase', async () => {
    uploadState = { phase: 'error', progress: 0, error: 'Archivo corrupto', jobId: null, version: null };
    render(<UploadDropzone documentId="doc-1" />);
    const pdf = new File(['%PDF-'], 'contrato.pdf', { type: 'application/pdf' });
    await userEvent.upload(screen.getByTestId('upload-input'), pdf);

    expect(screen.getByTestId('upload-error')).toHaveTextContent('Archivo corrupto');
  });
});
