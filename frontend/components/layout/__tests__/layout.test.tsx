import { describe, it, expect, beforeEach } from '@jest/globals';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import Footer from '../Footer';
import Header from '../Header';

import { useAuthStore } from '../../../lib/stores/authStore';

jest.mock('../../../lib/stores/authStore', () => ({
  useAuthStore: jest.fn(),
}));

const mockUseAuthStore = useAuthStore as unknown as jest.Mock;

const renderHeader = (authState: { isAuthenticated: boolean; signOut: jest.Mock }) => {
  mockUseAuthStore.mockImplementation((selector: (state: typeof authState) => unknown) =>
    selector(authState)
  );

  return render(<Header />);
};

describe('layout components', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders footer copy', () => {
    render(<Footer />);
    expect(screen.getByText(/Versiona — El Git de tus documentos/i)).toBeInTheDocument();
  });

  it('renders the public header links for signed out users', () => {
    renderHeader({ isAuthenticated: false, signOut: jest.fn() });

    expect(screen.getByRole('link', { name: 'Versiona' })).toHaveAttribute('href', '/');
    expect(screen.getAllByRole('link', { name: 'Comparar PDFs' })[0]).toHaveAttribute(
      'href',
      '/comparar'
    );
    expect(screen.getAllByRole('link', { name: 'Precios' })[0]).toHaveAttribute(
      'href',
      '/precios'
    );
    expect(screen.getAllByRole('link', { name: 'Manual' })[0]).toHaveAttribute(
      'href',
      '/manual'
    );
    expect(screen.getAllByRole('link', { name: 'Iniciar sesión' })[0]).toHaveAttribute(
      'href',
      '/sign-in'
    );
    expect(screen.getAllByRole('link', { name: 'Crear cuenta gratis' })[0]).toHaveAttribute(
      'href',
      '/sign-up'
    );
    expect(screen.queryByRole('button', { name: 'Salir' })).not.toBeInTheDocument();
  });

  it('renders header for authenticated users and signs out', async () => {
    const signOut = jest.fn();
    renderHeader({ isAuthenticated: true, signOut });

    expect(screen.getByRole('link', { name: 'Panel' })).toHaveAttribute('href', '/projects');
    const signOutButton = screen.getByRole('button', { name: 'Salir' });

    await userEvent.click(signOutButton);

    expect(signOut).toHaveBeenCalledTimes(1);
    expect(screen.queryByRole('link', { name: 'Iniciar sesión' })).not.toBeInTheDocument();
  });
});
