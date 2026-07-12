import { render, screen } from '@testing-library/react';

import { ActivityFeed } from '../ActivityFeed';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));

const mockGet = api.get as jest.Mock;

describe('ActivityFeed (kit 6)', () => {
  beforeEach(() => mockGet.mockReset());

  it('[ACT-F01] renders whitelisted events with actor and template', async () => {
    mockGet.mockResolvedValueOnce({
      data: {
        results: [
          {
            event_type: 'version.uploaded',
            actor_email: 'editor@versiona.test',
            payload: { number: 2 },
            created_at: '2026-07-12T10:00:00Z',
          },
          {
            event_type: 'seal.created',
            actor_email: 'reviewer@versiona.test',
            payload: { version: 1 },
            created_at: '2026-07-12T09:00:00Z',
          },
        ],
      },
    });

    render(<ActivityFeed projectId="p1" />);

    expect(await screen.findByTestId('activity-feed')).toBeInTheDocument();
    expect(screen.getByText('editor@versiona.test')).toBeInTheDocument();
    expect(screen.getByText('subió la versión v2')).toBeInTheDocument();
    expect(screen.getByText('selló la v1')).toBeInTheDocument();
  });

  it('[ACT-L01] shows the empty state', async () => {
    mockGet.mockResolvedValueOnce({ data: { results: [] } });

    render(<ActivityFeed projectId="p1" />);

    expect(await screen.findByText('Sin actividad todavía')).toBeInTheDocument();
  });

  it('degrades to empty on request failure', async () => {
    mockGet.mockRejectedValueOnce(new Error('403'));

    render(<ActivityFeed projectId="p1" />);

    expect(await screen.findByText('Sin actividad todavía')).toBeInTheDocument();
  });
});
