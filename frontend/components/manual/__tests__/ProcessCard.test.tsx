import { render, screen } from '@testing-library/react';

import ProcessCard from '../ProcessCard';
import type { ManualProcess } from '../../../lib/manual/types';

const createProcess = (overrides: Partial<ManualProcess> = {}): ManualProcess => ({
  id: 'seal-approve',
  title: { es: 'Aprueba con tu sello', en: 'Approve with your seal' },
  summary: { es: 'Firma la versión revisada.', en: 'Sign the reviewed version.' },
  why: { es: 'Da validez a la versión.', en: 'It grants the version validity.' },
  steps: {
    es: ['Abre la versión.', 'Presiona sellar.'],
    en: ['Open the version.', 'Press seal.'],
  },
  route: '/documentos/ver',
  tips: {
    es: ['Puedes sellar desde el detalle.'],
    en: ['You can seal from the detail view.'],
  },
  keywords: ['sello'],
  ...overrides,
});

describe('ProcessCard', () => {
  it('renders the process title and summary', () => {
    render(<ProcessCard process={createProcess()} locale="es" />);

    expect(screen.getByText('Aprueba con tu sello')).toBeInTheDocument();
    expect(screen.getByText('Firma la versión revisada.')).toBeInTheDocument();
  });

  it('renders the steps in order', () => {
    render(<ProcessCard process={createProcess({ tips: undefined })} locale="es" />);

    const steps = screen.getAllByRole('listitem').map((item) => item.textContent);
    expect(steps).toEqual(['Abre la versión.', 'Presiona sellar.']);
  });

  it('shows the route when the process defines one', () => {
    render(<ProcessCard process={createProcess()} locale="es" />);

    expect(screen.getByText('/documentos/ver')).toBeInTheDocument();
  });

  it('omits the route section when the process has no route', () => {
    render(<ProcessCard process={createProcess({ route: undefined })} locale="es" />);

    expect(screen.queryByText('Dónde encontrarlo')).not.toBeInTheDocument();
  });

  it('renders the tips list', () => {
    render(<ProcessCard process={createProcess()} locale="es" />);

    expect(screen.getByText('Tips útiles')).toBeInTheDocument();
    expect(screen.getByText('Puedes sellar desde el detalle.')).toBeInTheDocument();
  });

  it('omits tips when the process has none', () => {
    render(<ProcessCard process={createProcess({ tips: undefined })} locale="es" />);

    expect(screen.queryByText('Tips útiles')).not.toBeInTheDocument();
  });

  it('omits tips when the locale list is empty', () => {
    render(
      <ProcessCard
        process={createProcess({ tips: { es: [], en: ['Keep it handy.'] } })}
        locale="es"
      />
    );

    expect(screen.queryByText('Tips útiles')).not.toBeInTheDocument();
  });

  it('renders the English section labels for the en locale', () => {
    render(<ProcessCard process={createProcess()} locale="en" />);

    expect(screen.getByText('Why it matters')).toBeInTheDocument();
    expect(screen.getByText('How it works')).toBeInTheDocument();
  });
});
