import { publicApi } from '../../services/http';
import { usePublicCompareStore } from '../publicCompareStore';

jest.mock('../../services/http', () => ({
  publicApi: { get: jest.fn(), post: jest.fn() },
}));

const mockPost = publicApi.post as jest.Mock;
const mockGet = publicApi.get as jest.Mock;

const pdf = (name: string) =>
  new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], name, {
    type: 'application/pdf',
  });

describe('publicCompareStore', () => {
  beforeEach(() => {
    mockPost.mockReset();
    mockGet.mockReset();
    usePublicCompareStore.getState().reset();
  });

  it('submits two files and returns the public id', async () => {
    mockPost.mockResolvedValueOnce({ data: { public_id: 'abc', status: 'done' } });
    const store = usePublicCompareStore.getState();
    store.setSlot('a', pdf('v1.pdf'));
    store.setSlot('b', pdf('v2.pdf'));

    const id = await usePublicCompareStore.getState().submit();

    expect(id).toBe('abc');
    expect(usePublicCompareStore.getState().phase).toBe('processing');
  });

  it('rejects a non-pdf file client-side before uploading', async () => {
    const store = usePublicCompareStore.getState();
    store.setSlot('a', new File(['x'], 'foto.png', { type: 'image/png' }));
    store.setSlot('b', pdf('v2.pdf'));

    const id = await usePublicCompareStore.getState().submit();

    expect(id).toBeNull();
    expect(usePublicCompareStore.getState().errorKey).toBe('notPdf');
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('maps the 422 ocr_required response to the upsell error key', async () => {
    mockPost.mockRejectedValueOnce({
      response: { status: 422, data: { error_code: 'ocr_required' } },
    });
    const store = usePublicCompareStore.getState();
    store.setSlot('a', pdf('scan.pdf'));
    store.setSlot('b', pdf('v2.pdf'));

    await usePublicCompareStore.getState().submit();

    expect(usePublicCompareStore.getState().errorKey).toBe('scannedNeedsOcr');
  });

  it('maps a 429 response to the rate-limited error key', async () => {
    mockPost.mockRejectedValueOnce({ response: { status: 429, data: {} } });
    const store = usePublicCompareStore.getState();
    store.setSlot('a', pdf('v1.pdf'));
    store.setSlot('b', pdf('v2.pdf'));

    await usePublicCompareStore.getState().submit();

    expect(usePublicCompareStore.getState().errorKey).toBe('rateLimited');
  });

  it('loads a done comparison into the done phase', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        public_id: 'abc',
        status: 'done',
        error_code: '',
        file_a_name: 'v1.pdf',
        file_b_name: 'v2.pdf',
        created_at: 'x',
        expires_at: 'y',
        result: { counts: {}, summary_text: '', sections: [], meta: {} },
      },
    });

    await usePublicCompareStore.getState().load('abc');

    expect(usePublicCompareStore.getState().phase).toBe('done');
  });

  it('marks the expired result from a 410 response', async () => {
    mockGet.mockRejectedValueOnce({
      response: { status: 410, data: { error_code: 'expired' } },
    });

    await usePublicCompareStore.getState().load('abc');

    expect(usePublicCompareStore.getState().errorKey).toBe('expired');
  });
});
