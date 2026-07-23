import { render, screen, within } from '@testing-library/react';

import InboxPage from '../page';
import { api } from '@/lib/services/http';

jest.mock('@/lib/services/http', () => ({ api: { get: jest.fn(), post: jest.fn() } }));
jest.mock('@/lib/hooks/useRequireAuth', () => ({
  useRequireAuth: () => ({ isAuthenticated: true }),
}));

const mockGet = api.get as jest.Mock;

const RESPONSES: Record<string, unknown> = {
  'me/notifications/': { results: [], unread: 0 },
  'me/review_assignments/': { results: [] },
};

describe('InboxPage screen states (D1)', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockGet.mockImplementation((url: string) =>
      Promise.resolve({ data: RESPONSES[url] })
    );
  });

  it('[D1-L01] shows the up-to-date empty state when there are no notifications', async () => {
    render(<InboxPage />);

    const empty = await screen.findByTestId('empty-state');
    expect(within(empty).getByText('No tienes notificaciones')).toBeInTheDocument();
  });

  it('[D1-L01] explains what will land in the inbox later', async () => {
    render(<InboxPage />);

    const empty = await screen.findByTestId('empty-state');
    expect(
      within(empty).getByText('Aquí verás re-revisiones asignadas, sellos y aprobaciones.')
    ).toBeInTheDocument();
  });

  it('[D1-L01] hides the mark-all-read action when nothing is unread', async () => {
    render(<InboxPage />);

    await screen.findByTestId('empty-state');
    expect(screen.queryByTestId('mark-all-read')).not.toBeInTheDocument();
  });

  it('[D1-L01] hides the assigned reviews section when there is no pending work', async () => {
    render(<InboxPage />);

    await screen.findByTestId('empty-state');
    expect(screen.queryByTestId('inbox-assignments')).not.toBeInTheDocument();
  });
});
