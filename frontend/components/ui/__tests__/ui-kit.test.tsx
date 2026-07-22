import { describe, it, expect, beforeEach } from '@jest/globals';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { EmptyState } from '../EmptyState';
import { Modal } from '../Modal';
import { Skeleton } from '../Skeleton';
import { StatusBadge } from '../StatusBadge';
import { Tabs } from '../Tabs';
import { Toaster, useToastStore } from '../toast';

describe('StatusBadge', () => {
  it('renders its label with the given variant attribute', () => {
    render(<StatusBadge variant="approved">Aprobada</StatusBadge>);

    const badge = screen.getByTestId('status-badge');
    expect(badge).toHaveTextContent('Aprobada');
    expect(badge).toHaveAttribute('data-variant', 'approved');
  });

  it('defaults to the neutral variant', () => {
    render(<StatusBadge>Sin estado</StatusBadge>);

    expect(screen.getByTestId('status-badge')).toHaveAttribute('data-variant', 'neutral');
  });
});

describe('EmptyState', () => {
  it('renders title, description and action', () => {
    render(
      <EmptyState
        title="Sin proyectos"
        description="Crea tu primer proyecto para empezar."
        action={<button type="button">Crear proyecto</button>}
      />
    );

    expect(screen.getByRole('heading', { name: 'Sin proyectos' })).toBeInTheDocument();
    expect(screen.getByText('Crea tu primer proyecto para empezar.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Crear proyecto' })).toBeInTheDocument();
  });
});

describe('Skeleton', () => {
  it('is hidden from assistive technology', () => {
    render(<Skeleton className="h-4 w-24" />);

    expect(screen.getByTestId('skeleton')).toHaveAttribute('aria-hidden', 'true');
  });
});

describe('Modal', () => {
  it('renders nothing when closed', () => {
    render(
      <Modal open={false} onClose={jest.fn()} title="Confirmar">
        contenido
      </Modal>
    );

    expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  });

  it('calls onClose when the close button is clicked', async () => {
    const onClose = jest.fn();
    render(
      <Modal open onClose={onClose} title="Confirmar">
        contenido
      </Modal>
    );

    await userEvent.click(screen.getByRole('button', { name: 'Cerrar diálogo' }));

    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('calls onClose when Escape is pressed', async () => {
    const onClose = jest.fn();
    render(
      <Modal open onClose={onClose} title="Confirmar">
        contenido
      </Modal>
    );

    await userEvent.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalledTimes(1);
  });
});

describe('Tabs', () => {
  it('marks the active tab and notifies on change', async () => {
    const onChange = jest.fn();
    render(
      <Tabs
        items={[
          { id: 'sections', label: 'Secciones' },
          { id: 'seals', label: 'Sellos' },
        ]}
        active="sections"
        onChange={onChange}
      />
    );

    expect(screen.getByRole('tab', { name: 'Secciones' })).toHaveAttribute('aria-selected', 'true');

    await userEvent.click(screen.getByRole('tab', { name: 'Sellos' }));

    expect(onChange).toHaveBeenCalledWith('seals');
  });
});

describe('Toaster', () => {
  beforeEach(() => {
    useToastStore.getState().clear();
  });

  it('renders nothing when there are no toasts', () => {
    render(<Toaster />);

    expect(screen.queryByTestId('toaster')).not.toBeInTheDocument();
  });

  it('shows a pushed toast and dismisses it', async () => {
    render(<Toaster />);

    useToastStore.getState().push('Versión creada', 'success');

    expect(await screen.findByText('Versión creada')).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: 'Descartar aviso' }));

    expect(screen.queryByText('Versión creada')).not.toBeInTheDocument();
  });
});
