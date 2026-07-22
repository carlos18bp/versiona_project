import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { PublicDropzone } from '../PublicDropzone';
import { usePublicCompareStore } from '../../../lib/stores/publicCompareStore';

const pdf = (name: string) =>
  new File([new Uint8Array([0x25, 0x50, 0x44, 0x46])], name, {
    type: 'application/pdf',
  });

describe('PublicDropzone', () => {
  beforeEach(() => {
    usePublicCompareStore.getState().reset();
  });

  it('fills slot A from its picker input', async () => {
    render(<PublicDropzone />);

    await userEvent.upload(screen.getByTestId('public-file-a'), pdf('antes.pdf'));

    expect(screen.getByTestId('public-file-name-a')).toHaveTextContent('antes.pdf');
    expect(usePublicCompareStore.getState().slotA?.name).toBe('antes.pdf');
  });

  it('swaps the two selected files', async () => {
    render(<PublicDropzone />);
    await userEvent.upload(screen.getByTestId('public-file-a'), pdf('antes.pdf'));
    await userEvent.upload(screen.getByTestId('public-file-b'), pdf('despues.pdf'));

    await userEvent.click(screen.getByTestId('public-swap'));

    expect(usePublicCompareStore.getState().slotA?.name).toBe('despues.pdf');
    expect(usePublicCompareStore.getState().slotB?.name).toBe('antes.pdf');
  });
});
