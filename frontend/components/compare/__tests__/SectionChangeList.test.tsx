import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { SectionChangeList } from '../SectionChangeList';
import type { SectionChange } from '../../../lib/compare/sync';

const changes: SectionChange[] = [
  {
    stable_key: 'objeto-del-contrato',
    heading_from: '1. OBJETO DEL CONTRATO',
    heading_to: '1. OBJETO DEL CONTRATO',
    change_type: 'unchanged',
    similarity: 1,
    order_index: 0,
  },
  {
    stable_key: 'obligaciones-del-contratista',
    heading_from: '3. OBLIGACIONES DEL CONTRATISTA',
    heading_to: '3. OBLIGACIONES DEL CONTRATISTA',
    change_type: 'modified',
    similarity: 0.9,
    order_index: 1,
  },
  {
    stable_key: 'plazo-de-ejecucion',
    heading_from: '6. PLAZO DE EJECUCION',
    heading_to: '',
    change_type: 'removed',
    similarity: null,
    order_index: 2,
  },
];

describe('SectionChangeList', () => {
  it('[E1-F01] shows only changed sections when unchanged are hidden', () => {
    render(
      <SectionChangeList
        changes={changes}
        activeKey={null}
        hideUnchanged
        onToggleHideUnchanged={jest.fn()}
        onSelect={jest.fn()}
      />
    );

    expect(screen.getByTestId('section-obligaciones-del-contratista')).toBeInTheDocument();
    expect(screen.getByTestId('section-plazo-de-ejecucion')).toBeInTheDocument();
    expect(screen.queryByTestId('section-objeto-del-contrato')).not.toBeInTheDocument();
  });

  it('[E1-F01] lists unchanged sections when the toggle is off', () => {
    render(
      <SectionChangeList
        changes={changes}
        activeKey={null}
        hideUnchanged={false}
        onToggleHideUnchanged={jest.fn()}
        onSelect={jest.fn()}
      />
    );

    expect(screen.getByTestId('section-objeto-del-contrato')).toHaveAttribute(
      'data-change',
      'unchanged'
    );
  });

  it('[E1-F02] emits the section key on click', async () => {
    const onSelect = jest.fn();
    render(
      <SectionChangeList
        changes={changes}
        activeKey={null}
        hideUnchanged
        onToggleHideUnchanged={jest.fn()}
        onSelect={onSelect}
      />
    );

    await userEvent.click(screen.getByTestId('section-obligaciones-del-contratista'));

    expect(onSelect).toHaveBeenCalledWith('obligaciones-del-contratista');
  });

  it('[E1-F02] marks the active section with aria-current', () => {
    render(
      <SectionChangeList
        changes={changes}
        activeKey="plazo-de-ejecucion"
        hideUnchanged
        onToggleHideUnchanged={jest.fn()}
        onSelect={jest.fn()}
      />
    );

    expect(screen.getByTestId('section-plazo-de-ejecucion')).toHaveAttribute(
      'aria-current',
      'true'
    );
  });

  it('shows the removed section by its old heading', () => {
    render(
      <SectionChangeList
        changes={changes}
        activeKey={null}
        hideUnchanged
        onToggleHideUnchanged={jest.fn()}
        onSelect={jest.fn()}
      />
    );

    expect(screen.getByText('6. PLAZO DE EJECUCION')).toBeInTheDocument();
    expect(screen.getByTestId('section-plazo-de-ejecucion')).toHaveTextContent('Eliminada');
  });
});
