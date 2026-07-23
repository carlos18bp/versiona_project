import { render, screen } from '@testing-library/react';

import StagingPhaseBanner from '../StagingPhaseBanner';
import type { StagingBannerState } from '../../../lib/services/staging-banner';
import { useLocaleStore } from '../../../lib/stores/localeStore';

const createBannerState = (
  overrides: Partial<StagingBannerState> = {}
): StagingBannerState => ({
  is_visible: true,
  current_phase: 'design',
  phase_labels: { es: 'Fase de diseño', en: 'Design phase' },
  started_at: '2026-07-01T00:00:00Z',
  expires_at: '2026-07-30T00:00:00Z',
  days_remaining: 8,
  is_expired: false,
  contact_whatsapp: '+57 300 123 4567',
  contact_email: 'equipo@projectapp.co',
  ...overrides,
});

describe('StagingPhaseBanner', () => {
  beforeEach(() => {
    localStorage.clear();
    useLocaleStore.setState({ locale: 'es' });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('renders the phase label with the plural countdown', () => {
    render(<StagingPhaseBanner state={createBannerState({ days_remaining: 5 })} />);

    expect(screen.getByTestId('staging-phase-banner')).toHaveTextContent(
      'Fase de diseño — quedan 5 días para tu revisión'
    );
  });

  it('uses the singular copy for one remaining day', () => {
    render(<StagingPhaseBanner state={createBannerState({ days_remaining: 1 })} />);

    expect(screen.getByTestId('staging-phase-banner')).toHaveTextContent('queda 1 día');
  });

  it('treats a null countdown as zero days', () => {
    render(<StagingPhaseBanner state={createBannerState({ days_remaining: null })} />);

    expect(screen.getByTestId('staging-phase-banner')).toHaveTextContent('quedan 0 días');
  });

  it('renders the English copy for the en locale', () => {
    useLocaleStore.setState({ locale: 'en' });

    render(<StagingPhaseBanner state={createBannerState({ days_remaining: 3 })} />);

    expect(screen.getByTestId('staging-phase-banner')).toHaveTextContent(
      'Design phase — remain 3 days for your review'
    );
  });

  it('shows the development phase icon', () => {
    render(
      <StagingPhaseBanner state={createBannerState({ current_phase: 'development' })} />
    );

    expect(screen.getByTestId('staging-phase-banner')).toHaveTextContent('🛠️');
  });
});
