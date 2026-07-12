import axios from 'axios';

import { api } from '../../services/http';
import { useDocumentStore } from '../documentStore';

jest.mock('../../services/http', () => ({
  api: { post: jest.fn() },
}));
jest.mock('axios', () => ({
  __esModule: true,
  default: { put: jest.fn() },
}));

const mockApiPost = api.post as jest.Mock;
const mockAxiosPut = axios.put as jest.Mock;

describe('documentStore upload orchestration', () => {
  beforeEach(() => {
    mockApiPost.mockReset();
    mockAxiosPut.mockReset();
    useDocumentStore.getState().resetUpload();
  });

  const file = new File(['%PDF-fake'], 'contrato.pdf', { type: 'application/pdf' });

  it('walks intent → PUT → complete and lands on analyzing with a job id', async () => {
    mockApiPost
      .mockResolvedValueOnce({ data: { upload_id: 'u1', url: 'http://minio/put', max_bytes: 1 } })
      .mockResolvedValueOnce({ data: { job_id: 'job-9', version: { number: 1 } } });
    mockAxiosPut.mockResolvedValueOnce({});

    const result = await useDocumentStore.getState().uploadVersion('doc-1', file, 'primera');

    expect(result.phase).toBe('analyzing');
    expect(result.jobId).toBe('job-9');
    expect(mockAxiosPut).toHaveBeenCalledWith(
      'http://minio/put',
      file,
      expect.objectContaining({ headers: { 'Content-Type': 'application/pdf' } })
    );
    expect(mockApiPost).toHaveBeenLastCalledWith('documents/doc-1/versions/complete/', {
      upload_id: 'u1',
      message: 'primera',
    });
  });

  it('surfaces the backend rejection message on complete failure', async () => {
    mockApiPost
      .mockResolvedValueOnce({ data: { upload_id: 'u2', url: 'http://minio/put', max_bytes: 1 } })
      .mockRejectedValueOnce({
        response: { data: { error: 'El archivo es idéntico a la versión v1.' } },
      });
    mockAxiosPut.mockResolvedValueOnce({});

    const result = await useDocumentStore.getState().uploadVersion('doc-1', file, 'dup');

    expect(result.phase).toBe('error');
    expect(result.error).toContain('idéntico');
  });

  it('createDocument posts the title and returns the summary', async () => {
    mockApiPost.mockResolvedValueOnce({ data: { public_id: 'd1', title: 'Contrato' } });

    const doc = await useDocumentStore.getState().createDocument('proj-1', 'Contrato');

    expect(doc.public_id).toBe('d1');
    expect(mockApiPost).toHaveBeenCalledWith('projects/proj-1/documents/', { title: 'Contrato' });
  });
});
