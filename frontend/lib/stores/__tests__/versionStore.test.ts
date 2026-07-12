import { api } from '../../services/http';
import { useVersionStore } from '../versionStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn(), patch: jest.fn(), post: jest.fn(), delete: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPatch = api.patch as jest.Mock;
const mockDelete = api.delete as jest.Mock;
const mockPost = api.post as jest.Mock;

describe('versionStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPatch.mockReset();
    mockDelete.mockReset();
    mockPost.mockReset();
    useVersionStore.setState({ detail: null, fileUrl: null, isLoading: false, error: null });
  });

  it('fetchDetail stores the version detail', async () => {
    mockGet.mockResolvedValueOnce({ data: { public_id: 'v1', number: 1, sections: [] } });

    await useVersionStore.getState().fetchDetail('v1');

    expect(useVersionStore.getState().detail?.number).toBe(1);
  });

  it('fetchDetail surfaces backend errors', async () => {
    mockGet.mockRejectedValueOnce({ response: { data: { error: 'No encontrado' } } });

    await useVersionStore.getState().fetchDetail('v404');

    expect(useVersionStore.getState().error).toBe('No encontrado');
  });

  it('fetchFileUrl returns and stores the presigned url', async () => {
    mockGet.mockResolvedValueOnce({ data: { url: 'http://minio/file?sig=1' } });

    const url = await useVersionStore.getState().fetchFileUrl('v1');

    expect(url).toContain('sig=1');
    expect(useVersionStore.getState().fileUrl).toContain('sig=1');
  });

  it('editMessage patches and updates the loaded detail', async () => {
    useVersionStore.setState({ detail: { public_id: 'v1', message: 'antes' } as never });
    mockPatch.mockResolvedValueOnce({ data: { message: 'después' } });

    const ok = await useVersionStore.getState().editMessage('v1', 'después');

    expect(ok).toBe(true);
    expect(useVersionStore.getState().detail?.message).toBe('después');
  });

  it('editMessage returns false with the frozen-message error (I2b)', async () => {
    mockPatch.mockRejectedValueOnce({
      response: { data: { error: 'El mensaje quedó congelado' } },
    });

    const ok = await useVersionStore.getState().editMessage('v1', 'tarde');

    expect(ok).toBe(false);
    expect(useVersionStore.getState().error).toContain('congelado');
  });

  it('trashVersion and restoreVersion call their endpoints', async () => {
    mockDelete.mockResolvedValueOnce({});
    mockPost.mockResolvedValueOnce({});

    expect(await useVersionStore.getState().trashVersion('v1')).toBe(true);
    expect(await useVersionStore.getState().restoreVersion('v1')).toBe(true);
    expect(mockDelete).toHaveBeenCalledWith('versions/v1/');
    expect(mockPost).toHaveBeenCalledWith('versions/v1/restore/');
  });

  it('downloadUrl returns null and records the error on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('sin permiso'));

    const url = await useVersionStore.getState().downloadUrl('v1');

    expect(url).toBeNull();
    expect(useVersionStore.getState().error).toContain('sin permiso');
  });
});
