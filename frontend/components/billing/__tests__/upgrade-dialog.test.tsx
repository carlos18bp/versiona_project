import { render, screen } from '@testing-library/react';

import { UpgradeDialog } from '../UpgradeDialog';
import {
  maybeShowUpgradeDialog,
  useUpgradeDialogStore,
} from '../../../lib/stores/upgradeDialogStore';

describe('UpgradeDialog', () => {
  beforeEach(() => {
    useUpgradeDialogStore.setState({ isOpen: false, detail: null });
  });

  it('opens when maybeShowUpgradeDialog receives a 402 upgrade error', () => {
    const err = { response: { status: 402, data: { upgrade: true, error: 'Límite' } } };

    const handled = maybeShowUpgradeDialog(err);

    expect(handled).toBe(true);
    expect(useUpgradeDialogStore.getState().isOpen).toBe(true);
  });

  it('returns false and stays closed for non-402 errors', () => {
    const err = { response: { status: 500, data: { error: 'boom' } } };

    const handled = maybeShowUpgradeDialog(err);

    expect(handled).toBe(false);
    expect(useUpgradeDialogStore.getState().isOpen).toBe(false);
  });

  it('renders the plans CTA linking to /precios', () => {
    useUpgradeDialogStore.setState({ isOpen: true, detail: null });

    render(<UpgradeDialog />);

    expect(screen.getByTestId('upgrade-dialog-plans')).toHaveAttribute('href', '/precios');
  });

  it('shows the backend detail message inside the dialog', () => {
    useUpgradeDialogStore.setState({ isOpen: true, detail: 'Tu plan Gratis llegó a su límite' });

    render(<UpgradeDialog />);

    expect(screen.getByTestId('upgrade-dialog')).toHaveTextContent(
      'Tu plan Gratis llegó a su límite'
    );
  });
});
