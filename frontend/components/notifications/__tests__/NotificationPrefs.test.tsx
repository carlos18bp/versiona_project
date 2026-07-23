import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { NotificationPrefs } from '../NotificationPrefs';
import { api } from '../../../lib/services/http';
import { useLocaleStore } from '../../../lib/stores/localeStore';
import {
  useNotificationStore,
  type NotificationPref,
} from '../../../lib/stores/notificationStore';

jest.mock('../../../lib/services/http', () => ({
  api: { get: jest.fn(), patch: jest.fn() },
}));

const toast = jest.fn();
jest.mock('../../../components/ui/toast', () => ({
  useToast: () => ({ toast }),
}));

const mockGet = api.get as jest.Mock;
const mockPatch = api.patch as jest.Mock;

const createPref = (overrides: Partial<NotificationPref> = {}): NotificationPref => ({
  event_key: 'review_assigned',
  label_es: 'Te asignaron una revisión',
  label_en: 'You were assigned a review',
  mandatory_in_app: true,
  in_app: true,
  email: false,
  ...overrides,
});

const optionalPref = (overrides: Partial<NotificationPref> = {}): NotificationPref =>
  createPref({
    event_key: 'seal_invalidated',
    label_es: 'Sello invalidado',
    label_en: 'Seal invalidated',
    mandatory_in_app: false,
    ...overrides,
  });

const mockPrefs = (prefs: NotificationPref[]) => {
  mockGet.mockResolvedValue({ data: { preferences: prefs } });
};

describe('NotificationPrefs', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPatch.mockReset();
    toast.mockClear();
    localStorage.clear();
    useLocaleStore.setState({ locale: 'es' });
    useNotificationStore.setState({
      items: [],
      unread: 0,
      preferences: [],
      isLoading: false,
      error: null,
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders a row per fetched preference', async () => {
    mockPrefs([createPref(), optionalPref()]);

    render(<NotificationPrefs />);

    expect(await screen.findByText('Te asignaron una revisión')).toBeInTheDocument();
    expect(screen.getByText('Sello invalidado')).toBeInTheDocument();
  });

  it('renders the Spanish channel headers', async () => {
    mockPrefs([createPref()]);

    render(<NotificationPrefs />);

    expect(await screen.findByText('En la app')).toBeInTheDocument();
    expect(screen.getByText('Correo')).toBeInTheDocument();
  });

  it('disables the in-app toggle for mandatory events', async () => {
    mockPrefs([createPref()]);

    render(<NotificationPrefs />);

    expect(await screen.findByTestId('pref-review_assigned-in_app')).toBeDisabled();
  });

  it('marks mandatory events with the assigned-work hint', async () => {
    mockPrefs([createPref()]);

    render(<NotificationPrefs />);

    expect(
      await screen.findByText('(Obligatoria: es trabajo asignado)')
    ).toBeInTheDocument();
  });

  it('sends the email toggle to the preferences endpoint', async () => {
    mockPrefs([optionalPref()]);
    mockPatch.mockResolvedValueOnce({
      data: { preferences: [optionalPref({ email: true })] },
    });
    render(<NotificationPrefs />);

    await userEvent.click(await screen.findByTestId('pref-seal_invalidated-email'));

    expect(mockPatch).toHaveBeenCalledWith('me/notification_preferences/', {
      seal_invalidated: { email: true },
    });
  });

  it('sends the in-app toggle for optional events', async () => {
    mockPrefs([optionalPref()]);
    mockPatch.mockResolvedValueOnce({
      data: { preferences: [optionalPref({ in_app: false })] },
    });
    render(<NotificationPrefs />);

    await userEvent.click(await screen.findByTestId('pref-seal_invalidated-in_app'));

    expect(mockPatch).toHaveBeenCalledWith('me/notification_preferences/', {
      seal_invalidated: { in_app: false },
    });
  });

  it('reflects the patched preference state', async () => {
    mockPrefs([optionalPref()]);
    mockPatch.mockResolvedValueOnce({
      data: { preferences: [optionalPref({ email: true })] },
    });
    render(<NotificationPrefs />);

    await userEvent.click(await screen.findByTestId('pref-seal_invalidated-email'));

    await waitFor(() =>
      expect(screen.getByTestId('pref-seal_invalidated-email')).toBeChecked()
    );
  });

  it('surfaces a toast when the toggle fails', async () => {
    mockPrefs([optionalPref()]);
    mockPatch.mockRejectedValueOnce({
      response: { data: { error: 'Sin permiso para cambiar la preferencia' } },
    });
    render(<NotificationPrefs />);

    await userEvent.click(await screen.findByTestId('pref-seal_invalidated-email'));

    await waitFor(() =>
      expect(toast).toHaveBeenCalledWith('Sin permiso para cambiar la preferencia', 'error')
    );
  });

  it('renders English labels when the locale is en', async () => {
    mockPrefs([createPref()]);
    useLocaleStore.setState({ locale: 'en' });

    render(<NotificationPrefs />);

    expect(await screen.findByText('You were assigned a review')).toBeInTheDocument();
  });
});
