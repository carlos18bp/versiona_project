import { render, screen } from '@testing-library/react';

import StagingExpiredOverlay from '../StagingExpiredOverlay';
import type { StagingBannerState } from '../../../lib/services/staging-banner';
import { useLocaleStore } from '../../../lib/stores/localeStore';

const createBannerState = (
  overrides: Partial<StagingBannerState> = {}
): StagingBannerState => ({
  is_visible: true,
  current_phase: 'design',
  phase_labels: { es: 'Diseño', en: 'Design' },
  started_at: '2026-07-01T00:00:00Z',
  expires_at: '2026-07-10T00:00:00Z',
  days_remaining: 0,
  is_expired: true,
  contact_whatsapp: '+57 300 123-4567',
  contact_email: 'equipo@projectapp.co',
  ...overrides,
});

describe('StagingExpiredOverlay', () => {
  beforeEach(() => {
    localStorage.clear();
    useLocaleStore.setState({ locale: 'es' });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders the expired title with the lowercased phase label', () => {
    render(<StagingExpiredOverlay state={createBannerState()} />);

    expect(screen.getByRole('dialog')).toHaveTextContent(
      'La etapa de diseño ha finalizado'
    );
  });

  it('links WhatsApp using only the phone digits', () => {
    render(<StagingExpiredOverlay state={createBannerState()} />);

    expect(screen.getByTestId('staging-expired-whatsapp')).toHaveAttribute(
      'href',
      'https://wa.me/573001234567'
    );
  });

  it('links the contact email', () => {
    render(<StagingExpiredOverlay state={createBannerState()} />);

    expect(screen.getByTestId('staging-expired-email')).toHaveAttribute(
      'href',
      'mailto:equipo@projectapp.co'
    );
  });

  it('renders the English title for the en locale', () => {
    useLocaleStore.setState({ locale: 'en' });

    render(<StagingExpiredOverlay state={createBannerState()} />);

    expect(screen.getByRole('dialog')).toHaveTextContent('The design has ended');
  });
});
