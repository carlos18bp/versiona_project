import { api } from '../../services/http';
import { useLocaleStore } from '../localeStore';
import { useProfileStore } from '../profileStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn(), patch: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPatch = api.patch as jest.Mock;

const profile = {
  email: 'ana@example.com',
  first_name: 'Ana',
  last_name: 'Pérez',
  phone: '',
  language: 'en' as const,
  timezone: 'Europe/Madrid',
};

describe('profileStore', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPatch.mockReset();
    useProfileStore.setState({ profile: null, isLoading: false, isSaving: false, error: null });
    useLocaleStore.getState().setLocale('es');
  });

  it('fetchProfile stores the profile and syncs the UI locale', async () => {
    mockGet.mockResolvedValueOnce({ data: profile });

    await useProfileStore.getState().fetchProfile();

    expect(useProfileStore.getState().profile?.email).toBe('ana@example.com');
    expect(useLocaleStore.getState().locale).toBe('en');
  });

  it('updateProfile patches and returns true on success', async () => {
    mockPatch.mockResolvedValueOnce({ data: { ...profile, language: 'es' } });

    const ok = await useProfileStore.getState().updateProfile({ language: 'es' });

    expect(ok).toBe(true);
    expect(useLocaleStore.getState().locale).toBe('es');
  });

  it('updateProfile surfaces the field error on invalid timezone', async () => {
    mockPatch.mockRejectedValueOnce({
      response: { data: { timezone: ['Zona horaria IANA inválida.'] } },
    });

    const ok = await useProfileStore.getState().updateProfile({ timezone: 'Marte/Colonia' });

    expect(ok).toBe(false);
    expect(useProfileStore.getState().error).toContain('inválida');
  });
});
