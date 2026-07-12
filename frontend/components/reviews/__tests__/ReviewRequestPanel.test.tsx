import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ReviewRequestPanel } from '../ReviewRequestPanel';
import type { ReviewRequestRow } from '../../../lib/stores/reviewStore';

const fetchRequests = jest.fn();
const fetchMembers = jest.fn();
const createRequest = jest.fn();
const cancelRequest = jest.fn();
let state: Record<string, unknown> = {};

jest.mock('../../../lib/stores/reviewStore', () => ({
  useReviewStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) => selector(state),
    { getState: () => ({ error: null }) }
  ),
}));

const openRequest: ReviewRequestRow = {
  public_id: 'r1',
  status: 'open',
  message: 'enfócate en las multas',
  requested_by_email: 'editor@versiona.test',
  version_number: 1,
  assignments: [
    { reviewer_email: 'reviewer@versiona.test', scope: 'all', status: 'pending',
      completed_at: null },
  ],
  created_at: '2026-07-12T10:00:00Z',
  closed_at: null,
};

function setState(over: Record<string, unknown> = {}) {
  state = {
    requests: [],
    members: [
      { id: 1, email: 'reviewer@versiona.test', first_name: 'R', role: 'reviewer' },
      { id: 2, email: 'viewer@versiona.test', first_name: 'V', role: 'viewer' },
    ],
    isSubmitting: false,
    fetchRequests,
    fetchMembers,
    createRequest,
    cancelRequest,
    ...over,
  };
}

describe('ReviewRequestPanel (D1)', () => {
  beforeEach(() => {
    createRequest.mockReset();
    setState();
  });

  it('[D1-F04-ui] shows the open request with assignment progress', () => {
    setState({ requests: [openRequest] });

    render(<ReviewRequestPanel versionId="v1" projectId="p1" canRequest />);

    expect(screen.getByText('Revisión abierta')).toBeInTheDocument();
    expect(screen.getByTestId('assignment-reviewer@versiona.test')).toHaveTextContent(
      'Pendiente de'
    );
    expect(screen.queryByTestId('request-review')).not.toBeInTheDocument();
  });

  it('[D1-F01-ui] the picker only offers reviewer/admin members', async () => {
    render(<ReviewRequestPanel versionId="v1" projectId="p1" canRequest />);

    await userEvent.click(screen.getByTestId('request-review'));

    expect(screen.getByTestId('pick-reviewer-reviewer@versiona.test')).toBeInTheDocument();
    expect(
      screen.queryByTestId('pick-reviewer-viewer@versiona.test')
    ).not.toBeInTheDocument();
  });

  it('[D1-F01-ui] sends the request with picked reviewers and message', async () => {
    createRequest.mockResolvedValue(true);
    render(<ReviewRequestPanel versionId="v1" projectId="p1" canRequest />);

    await userEvent.click(screen.getByTestId('request-review'));
    await userEvent.click(screen.getByTestId('pick-reviewer-reviewer@versiona.test'));
    await userEvent.type(screen.getByTestId('review-message'), 'urgente');
    await userEvent.click(screen.getByTestId('send-review-request'));

    expect(createRequest).toHaveBeenCalledWith('v1', [1], 'urgente');
  });

  it('[D1-P02] hides the request button from non-editors', () => {
    render(<ReviewRequestPanel versionId="v1" projectId="p1" canRequest={false} />);

    expect(screen.queryByTestId('request-review')).not.toBeInTheDocument();
  });
});
