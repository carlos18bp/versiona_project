import { api } from '../../services/http';
import { selectActiveOrg, useOrgStore } from '../orgStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

const orgs = [
  { public_id: 'o1', name: 'Personal', slug: 'personal', kind: 'personal', role: 'owner' },
  { public_id: 'o2', name: 'Acme', slug: 'acme', kind: 'team', role: 'member' },
];

describe('orgStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    useOrgStore.setState({ orgs: [], activeOrgId: null, isLoading: false, error: null });
  });

  it('fetchOrgs stores the list and defaults the active org to the first', async () => {
    mockGet.mockResolvedValueOnce({ data: { results: orgs } });

    await useOrgStore.getState().fetchOrgs();

    expect(useOrgStore.getState().orgs).toHaveLength(2);
    expect(useOrgStore.getState().activeOrgId).toBe('o1');
    expect(selectActiveOrg(useOrgStore.getState())?.name).toBe('Personal');
  });

  it('fetchOrgs keeps a still-valid active org selection', async () => {
    useOrgStore.setState({ activeOrgId: 'o2' });
    mockGet.mockResolvedValueOnce({ data: { results: orgs } });

    await useOrgStore.getState().fetchOrgs();

    expect(useOrgStore.getState().activeOrgId).toBe('o2');
  });

  it('fetchOrgs surfaces the error message on failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('red caída'));

    await useOrgStore.getState().fetchOrgs();

    expect(useOrgStore.getState().error).toContain('red caída');
    expect(useOrgStore.getState().isLoading).toBe(false);
  });

  it('setActiveOrg switches the selection', () => {
    useOrgStore.setState({ orgs: orgs as never });

    useOrgStore.getState().setActiveOrg('o2');

    expect(useOrgStore.getState().activeOrgId).toBe('o2');
  });
});
