import { render, screen } from '@testing-library/react';

import { PublicCompareCta } from '../PublicCompareCta';

describe('PublicCompareCta', () => {
  it('renders the signup pitch title', () => {
    render(<PublicCompareCta />);

    expect(
      screen.getByText('¿Quieres guardar, versionar y sellar este documento?')
    ).toBeInTheDocument();
  });

  it('renders the Pro trial pitch body', () => {
    render(<PublicCompareCta />);

    expect(screen.getByTestId('public-compare-cta')).toHaveTextContent(
      '14 días de prueba Pro'
    );
  });

  it('links the CTA button to the sign-up page', () => {
    render(<PublicCompareCta />);

    expect(screen.getByRole('link', { name: 'Crear cuenta gratis' })).toHaveAttribute(
      'href',
      '/sign-up'
    );
  });
});
