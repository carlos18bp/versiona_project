import { api } from '../../services/http';
import { useSealStore } from '../sealStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

const seal = {
  public_id: 's1',
  reviewer_email: 'revisor@versiona.test',
  version_number: 1,
  covers_all: false,
  covered_keys: ['objeto-del-contrato'],
  key_id: 'k1',
  is_active: true,
  revoked_at: null,
  created_at: '2026-07-12T10:00:00Z',
};

describe('sealStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    useSealStore.setState({
      seals: [], validityRecords: [], pendingPlan: [],
      isLoading: false, isSubmitting: false, error: null,
    });
  });

  it('fetchSeals stores seals and validity records', async () => {
    mockGet.mockResolvedValueOnce({
      data: { seals: [seal], validity_records: [{ decision: 'preserved', seal }] },
    });

    await useSealStore.getState().fetchSeals('v1');

    expect(useSealStore.getState().seals).toHaveLength(1);
    expect(useSealStore.getState().validityRecords[0].decision).toBe('preserved');
  });

  it('[D4-F01-ui] createSeal posts sections and refreshes', async () => {
    mockPost.mockResolvedValueOnce({ data: seal });
    mockGet.mockResolvedValueOnce({ data: { seals: [seal], validity_records: [] } });

    const ok = await useSealStore.getState().createSeal('v1', {
      coversAll: false,
      sectionKeys: ['objeto-del-contrato'],
    });

    expect(ok).toBe(true);
    expect(mockPost).toHaveBeenCalledWith('versions/v1/seals/', {
      covers_all: false,
      section_keys: ['objeto-del-contrato'],
    });
  });

  it('createSeal surfaces the backend rejection', async () => {
    mockPost.mockRejectedValueOnce({
      response: { data: { error: 'Ya tienes un sello activo en esta versión.' } },
    });

    const ok = await useSealStore.getState().createSeal('v1', { coversAll: true });

    expect(ok).toBe(false);
    expect(useSealStore.getState().error).toContain('sello activo');
  });

  it('[D5-A04-ui] confirmPlan posts decisions and clears the pending plan', async () => {
    useSealStore.setState({ pendingPlan: [{ decision: 'pending_confirmation' } as never] });
    mockPost.mockResolvedValueOnce({ data: { resolved: [] } });
    mockGet.mockResolvedValueOnce({ data: { seals: [], validity_records: [] } });

    const ok = await useSealStore.getState().confirmPlan('v2', { s1: 'invalidated' });

    expect(ok).toBe(true);
    expect(mockPost).toHaveBeenCalledWith('versions/v2/seal_plan/', {
      decisions: { s1: 'invalidated' },
    });
    expect(useSealStore.getState().pendingPlan).toEqual([]);
  });

  it('verifySeal returns the offline verification material', async () => {
    mockGet.mockResolvedValueOnce({
      data: { signature_valid: true, binds_version_sha256: true, algorithm: 'Ed25519' },
    });

    const result = await useSealStore.getState().verifySeal('v1', 's1');

    expect(result?.signature_valid).toBe(true);
    expect(result?.algorithm).toBe('Ed25519');
  });
});
