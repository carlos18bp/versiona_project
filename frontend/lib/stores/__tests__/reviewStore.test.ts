import { api } from '../../services/http';
import { useReviewStore } from '../reviewStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

describe('reviewStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    useReviewStore.setState({
      requests: [], assignments: [], context: null, members: [],
      isLoading: false, isSubmitting: false, error: null,
    });
  });

  it('[D1-F01-ui] createRequest posts reviewers and refreshes the list', async () => {
    mockPost.mockResolvedValueOnce({ data: { public_id: 'r1' } });
    mockGet.mockResolvedValueOnce({ data: { results: [{ public_id: 'r1', status: 'open' }] } });

    const ok = await useReviewStore.getState().createRequest('v1', [7], 'urgente');

    expect(ok).toBe(true);
    expect(mockPost).toHaveBeenCalledWith('versions/v1/reviews/', {
      reviewer_ids: [7],
      message: 'urgente',
    });
    expect(useReviewStore.getState().requests).toHaveLength(1);
  });

  it('createRequest surfaces the domain rejection', async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { error: 'Esta versión ya tiene una revisión abierta.' } },
    });

    const ok = await useReviewStore.getState().createRequest('v1', [7], '');

    expect(ok).toBe(false);
    expect(useReviewStore.getState().error).toContain('revisión abierta');
  });

  it('[D1-F04-ui] fetchAssignments fills the reviewer inbox', async () => {
    mockGet.mockResolvedValueOnce({
      data: { results: [{ review: 'r1', document_title: 'Contrato', version_number: 1 }] },
    });

    await useReviewStore.getState().fetchAssignments();

    expect(useReviewStore.getState().assignments[0].document_title).toBe('Contrato');
  });

  it('[D2-F01-ui] fetchContext stores the assisted-review payload', async () => {
    mockGet.mockResolvedValueOnce({
      data: { my_last_sealed_version: 1, changed: [{ stable_key: 'multas' }], unchanged: [] },
    });

    await useReviewStore.getState().fetchContext('v2');

    expect(useReviewStore.getState().context?.my_last_sealed_version).toBe(1);
  });

  it('fetchContext degrades to null on error', async () => {
    mockGet.mockRejectedValueOnce(new Error('boom'));

    await useReviewStore.getState().fetchContext('v2');

    expect(useReviewStore.getState().context).toBeNull();
  });

  it('cancelRequest posts and reloads', async () => {
    mockPost.mockResolvedValueOnce({ data: {} });
    mockGet.mockResolvedValueOnce({ data: { results: [] } });

    const ok = await useReviewStore.getState().cancelRequest('v1', 'r1');

    expect(ok).toBe(true);
    expect(mockPost).toHaveBeenCalledWith('versions/v1/reviews/r1/cancel/');
  });

  it('fetchMembers stores the picker list', async () => {
    mockGet.mockResolvedValueOnce({
      data: { results: [{ id: 1, email: 'r@x.co', role: 'reviewer' }] },
    });

    await useReviewStore.getState().fetchMembers('p1');

    expect(useReviewStore.getState().members).toHaveLength(1);
  });
});
