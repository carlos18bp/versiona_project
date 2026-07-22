import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { SealActionBar } from '../SealActionBar';

const createSeal = jest.fn();
jest.mock('../../../lib/stores/sealStore', () => ({
  useSealStore: Object.assign(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ createSeal, isSubmitting: false, error: null }),
    { getState: () => ({ error: null }) }
  ),
}));
const toast = jest.fn();
jest.mock('../../../components/ui/toast', () => ({
  useToast: () => ({ toast }),
}));

const sections = [
  { stable_key: 'objeto-del-contrato', heading_text: '1. OBJETO', level: 1,
    order_index: 0, page_start: 1, page_end: 1, char_count: 10, bboxes: [], body_hash: 'a' },
  { stable_key: 'definiciones', heading_text: '2. DEFINICIONES', level: 1,
    order_index: 1, page_start: 1, page_end: 1, char_count: 10, bboxes: [], body_hash: 'b' },
];

describe('SealActionBar (D4)', () => {
  beforeEach(() => {
    createSeal.mockReset();
    toast.mockReset();
  });

  it('[D4-F01-ui] seals the whole document in one click', async () => {
    createSeal.mockResolvedValue(true);
    render(<SealActionBar versionId="v1" sections={sections} />);

    await userEvent.click(screen.getByTestId('seal-all'));

    expect(createSeal).toHaveBeenCalledWith('v1', { coversAll: true, sectionKeys: [] });
  });

  it('[D4-F01b-ui] the section picker requires at least one selection', async () => {
    createSeal.mockResolvedValue(true);
    render(<SealActionBar versionId="v1" sections={sections} />);

    await userEvent.click(screen.getByTestId('seal-sections-open'));
    expect(screen.getByTestId('seal-picked')).toBeDisabled();

    await userEvent.click(screen.getByTestId('pick-objeto-del-contrato'));
    await userEvent.click(screen.getByTestId('pick-definiciones'));
    await userEvent.click(screen.getByTestId('seal-picked'));

    expect(createSeal).toHaveBeenCalledWith('v1', {
      coversAll: false,
      sectionKeys: ['objeto-del-contrato', 'definiciones'],
    });
  });

  it('[D4-E03-ui] surfaces the double-seal rejection', async () => {
    createSeal.mockResolvedValue(false);
    render(<SealActionBar versionId="v1" sections={sections} />);

    await userEvent.click(screen.getByTestId('seal-all'));

    expect(toast).toHaveBeenCalledWith(expect.any(String), 'error');
  });
});
