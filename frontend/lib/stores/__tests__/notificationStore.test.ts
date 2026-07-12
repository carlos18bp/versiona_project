import { api } from '../../services/http';
import { useNotificationStore } from '../notificationStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn(), post: jest.fn(), patch: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;
const mockPatch = api.patch as jest.Mock;

const item = {
  public_id: 'n1',
  event_key: 'seal.invalidated',
  title: 'Tu sello requiere re-revisión',
  body: '',
  link: '/inbox',
  payload: {},
  read_at: null,
  created_at: '2026-07-12T10:00:00Z',
};

describe('notificationStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    mockPatch.mockReset();
    useNotificationStore.setState({
      items: [], unread: 0, preferences: [], isLoading: false, error: null,
    });
  });

  it('fetch stores items and the unread count', async () => {
    mockGet.mockResolvedValueOnce({ data: { results: [item], unread: 1 } });

    await useNotificationStore.getState().fetch();

    expect(useNotificationStore.getState().items).toHaveLength(1);
    expect(useNotificationStore.getState().unread).toBe(1);
  });

  it('markRead flips the item locally and decrements unread', async () => {
    useNotificationStore.setState({ items: [item], unread: 1 });
    mockPost.mockResolvedValueOnce({ data: {} });

    await useNotificationStore.getState().markRead('n1');

    expect(useNotificationStore.getState().items[0].read_at).not.toBeNull();
    expect(useNotificationStore.getState().unread).toBe(0);
  });

  it('[NTF-E01-ui] updatePreference reverts on backend rejection', async () => {
    mockPatch.mockRejectedValueOnce({
      response: { data: { error: 'no puede silenciarse: es trabajo asignado' } },
    });
    mockGet.mockResolvedValueOnce({ data: { preferences: [] } });

    const ok = await useNotificationStore
      .getState()
      .updatePreference('seal.invalidated', 'in_app', false);

    expect(ok).toBe(false);
    expect(useNotificationStore.getState().error).toContain('trabajo asignado');
    expect(mockGet).toHaveBeenCalledWith('me/notification_preferences/');
  });

  it('updatePreference stores the merged preferences on success', async () => {
    mockPatch.mockResolvedValueOnce({
      data: {
        preferences: [
          { event_key: 'seal.preserved', in_app: true, email: false,
            mandatory_in_app: false, label_es: 'x', label_en: 'x' },
        ],
      },
    });

    const ok = await useNotificationStore
      .getState()
      .updatePreference('seal.preserved', 'in_app', true);

    expect(ok).toBe(true);
    expect(useNotificationStore.getState().preferences[0].in_app).toBe(true);
  });
});
