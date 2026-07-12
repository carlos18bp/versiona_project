import { describe, it, expect } from '@jest/globals';
import { render, screen } from '@testing-library/react';

import HomePage from '../page';

describe('HomePage', () => {
  it('renders the Versiona headline', () => {
    render(<HomePage />);
    expect(
      screen.getByRole('heading', { name: 'El Git de tus documentos' })
    ).toBeInTheDocument();
  });

  it('links the primary call to action to sign-up', () => {
    render(<HomePage />);
    expect(screen.getByRole('link', { name: 'Crear cuenta gratis' })).toHaveAttribute(
      'href',
      '/sign-up'
    );
  });
});
