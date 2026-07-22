import { act } from '@testing-library/react';

import { api } from '../../services/http';
import { useJobStore } from '../jobStore';

jest.mock('../../services/http', () => ({
  api: { get: jest.fn() },
}));

const mockGet = api.get as jest.Mock;

describe('jobStore', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    mockGet.mockReset();
    useJobStore.setState({ jobs: {} });
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('polls until the job reaches done and notifies once', async () => {
    mockGet
      .mockResolvedValueOnce({ data: { public_id: 'j1', status: 'running' } })
      .mockResolvedValueOnce({ data: { public_id: 'j1', status: 'done', result: { ok: 1 } } });
    const onFinish = jest.fn();

    useJobStore.getState().track('j1', onFinish);

    await act(async () => {
      await jest.advanceTimersByTimeAsync(0); // first poll
      await jest.advanceTimersByTimeAsync(2000); // second poll (done)
    });

    expect(onFinish).toHaveBeenCalledTimes(1);
    expect(useJobStore.getState().jobs.j1.status).toBe('done');
  });

  it('stops polling when the job fails', async () => {
    mockGet.mockResolvedValue({ data: { public_id: 'j2', status: 'failed', error: 'boom' } });
    const onFinish = jest.fn();

    useJobStore.getState().track('j2', onFinish);

    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
      await jest.advanceTimersByTimeAsync(30000);
    });

    expect(onFinish).toHaveBeenCalledTimes(1);
    expect(mockGet).toHaveBeenCalledTimes(1);
  });

  it('does not double-track the same job id', async () => {
    mockGet.mockResolvedValue({ data: { public_id: 'j3', status: 'running' } });

    useJobStore.getState().track('j3');
    useJobStore.getState().track('j3');

    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
    });

    expect(mockGet).toHaveBeenCalledTimes(1);
    useJobStore.getState().clear('j3');
  });

  it('clear removes the job and its timer', async () => {
    mockGet.mockResolvedValue({ data: { public_id: 'j4', status: 'running' } });
    useJobStore.getState().track('j4');
    await act(async () => {
      await jest.advanceTimersByTimeAsync(0);
    });

    useJobStore.getState().clear('j4');

    expect(useJobStore.getState().jobs.j4).toBeUndefined();
    await act(async () => {
      await jest.advanceTimersByTimeAsync(60000);
    });
    expect(mockGet).toHaveBeenCalledTimes(1);
  });
});
