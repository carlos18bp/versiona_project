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

  it('links the compare CTA to the public comparator', () => {
    render(<HomePage />);
    expect(screen.getByTestId('hero-cta-compare')).toHaveAttribute('href', '/comparar');
  });

  it('links the signup CTA with the trial promise to sign-up', () => {
    render(<HomePage />);
    const cta = screen.getByTestId('hero-cta-signup');
    expect(cta).toHaveAttribute('href', '/sign-up');
    expect(cta).toHaveTextContent('14 días');
  });

  it('renders the honest marketing sections', () => {
    render(<HomePage />);
    expect(screen.getByTestId('how-it-works')).toBeInTheDocument();
    expect(screen.getByTestId('features-grid')).toBeInTheDocument();
    expect(screen.getByTestId('tech-strip')).toBeInTheDocument();
    expect(screen.getByTestId('pricing-preview')).toBeInTheDocument();
    expect(screen.getByTestId('landing-faq')).toBeInTheDocument();
  });
});
