import { api } from '../../services/http';
import { useObservationStore } from '../observationStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

describe('observationStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    useObservationStore.setState({
      items: [], isLoading: false, isSubmitting: false, error: null,
    });
  });

  it('fetch stores the threads', async () => {
    mockGet.mockResolvedValueOnce({
      data: { results: [{ public_id: 'o1', status: 'open' }] },
    });

    await useObservationStore.getState().fetch('v1');

    expect(useObservationStore.getState().items).toHaveLength(1);
  });

  it('[D3-F01-ui] create posts the section anchor and refreshes', async () => {
    mockPost.mockResolvedValueOnce({ data: { public_id: 'o1' } });
    mockGet.mockResolvedValueOnce({ data: { results: [{ public_id: 'o1' }] } });

    const ok = await useObservationStore.getState().create('v1', {
      body: 'Multa baja',
      sectionKey: 'obligaciones-del-contratista',
    });

    expect(ok).toBe(true);
    expect(mockPost).toHaveBeenCalledWith('versions/v1/observations/', {
      body: 'Multa baja',
      section_key: 'obligaciones-del-contratista',
    });
  });

  it('[D3-E01-ui] setStatus surfaces the I14 rejection', async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { error: 'Transición inválida: open → resolved (I14 …)' } },
    });

    const ok = await useObservationStore.getState().setStatus('v1', 'o1', 'resolved');

    expect(ok).toBe(false);
    expect(useObservationStore.getState().error).toContain('I14');
  });

  it('reply posts and refreshes the thread', async () => {
    mockPost.mockResolvedValueOnce({ data: {} });
    mockGet.mockResolvedValueOnce({ data: { results: [] } });

    const ok = await useObservationStore.getState().reply('v1', 'o1', 'Corregido');

    expect(ok).toBe(true);
    expect(mockPost).toHaveBeenCalledWith('observations/o1/replies/', { body: 'Corregido' });
  });
});
