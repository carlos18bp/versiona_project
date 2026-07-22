import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ProjectAdminActions } from '../ProjectAdminActions';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({
  api: { get: jest.fn(), post: jest.fn(), delete: jest.fn() },
}));
const push = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push }),
}));
const toast = jest.fn();
jest.mock('../../../components/ui/toast', () => ({
  useToast: () => ({ toast }),
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;
const mockDelete = api.delete as jest.Mock;

function prime(role: string, status = 'active') {
  mockGet.mockResolvedValue({
    data: { name: 'Torre', status, effective_role: role },
  });
}

describe('ProjectAdminActions (B4)', () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockPost.mockReset();
    mockDelete.mockReset();
    toast.mockReset();
    push.mockReset();
  });

  it('[B4-P02] renders nothing for non-admins', async () => {
    prime('editor');

    render(<ProjectAdminActions projectId="p1" />);

    await new Promise((resolve) => setTimeout(resolve, 0));
    expect(screen.queryByTestId('project-admin-actions')).not.toBeInTheDocument();
  });

  it('[B4-F01-ui] archives and shows the read-only banner', async () => {
    prime('admin');
    mockPost.mockResolvedValueOnce({});

    render(<ProjectAdminActions projectId="p1" />);
    await userEvent.click(await screen.findByTestId('archive-project'));

    expect(mockPost).toHaveBeenCalledWith('projects/p1/archive/');
  });

  it('[B4-F02-ui] deleting demands the exact project name', async () => {
    prime('admin');
    mockDelete.mockResolvedValueOnce({});

    render(<ProjectAdminActions projectId="p1" />);
    await userEvent.click(await screen.findByTestId('trash-project'));

    const submit = screen.getByTestId('type-to-confirm-submit');
    expect(submit).toBeDisabled();
    await userEvent.type(screen.getByTestId('type-to-confirm-input'), 'Torre');
    await userEvent.click(submit);

    expect(mockDelete).toHaveBeenCalledWith('projects/p1/', {
      data: { confirm_name: 'Torre' },
    });
    expect(push).toHaveBeenCalledWith('/projects');
  });

  it('[B4-E01-ui] T4: the sealed-project rejection surfaces', async () => {
    prime('admin');
    mockDelete.mockRejectedValueOnce({
      response: { data: { error: 'Proyecto con sellos: solo puede archivarse (T4).' } },
    });

    render(<ProjectAdminActions projectId="p1" />);
    await userEvent.click(await screen.findByTestId('trash-project'));
    await userEvent.type(screen.getByTestId('type-to-confirm-input'), 'Torre');
    await userEvent.click(screen.getByTestId('type-to-confirm-submit'));

    expect(toast).toHaveBeenCalledWith(expect.stringContaining('T4'), 'error');
    expect(push).not.toHaveBeenCalled();
  });
});
