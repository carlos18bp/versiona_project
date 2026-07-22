import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { PublicCompareResult } from '../PublicCompareResult';
import type { PublicComparisonDetail } from '../../../lib/stores/publicCompareStore';

const detail: PublicComparisonDetail = {
  public_id: 'abc',
  status: 'done',
  error_code: '',
  file_a_name: 'contrato_v1.pdf',
  file_b_name: 'contrato_v2.pdf',
  created_at: '2026-07-22T10:00:00Z',
  expires_at: '2026-07-23T10:00:00Z',
  result: {
    counts: { unchanged: 6, modified: 2, added: 1, removed: 1, renamed_only: 0 },
    summary_text: '2 modificadas, 1 eliminada, 1 agregada',
    meta: { page_count_a: 3, page_count_b: 3 },
    sections: [
      {
        stable_key: 'valor-y-forma-de-pago',
        heading_from: 'Valor y forma de pago',
        heading_to: 'Valor y forma de pago',
        change_type: 'modified',
        similarity: 0.91,
        order_index: 3,
        word_diff: [
          { op: 'equal', text: 'El valor es ' },
          { op: 'delete', text: 'diez' },
          { op: 'insert', text: 'doce' },
        ],
      },
    ],
  },
};

describe('PublicCompareResult', () => {
  it('renders the truth-table counts from the result payload', () => {
    render(<PublicCompareResult detail={detail} />);

    expect(screen.getByTestId('count-modified')).toHaveTextContent('2');
    expect(screen.getByTestId('count-added')).toHaveTextContent('1');
    expect(screen.getByTestId('count-removed')).toHaveTextContent('1');
    expect(screen.getByText('2 modificadas, 1 eliminada, 1 agregada')).toBeInTheDocument();
  });

  it('renders insert and delete word-diff ops for a selected section', async () => {
    render(<PublicCompareResult detail={detail} />);

    await userEvent.click(screen.getByText('Valor y forma de pago'));

    const diff = screen.getByTestId('public-word-diff');
    expect(diff.querySelector('ins')).toHaveTextContent('doce');
    expect(diff.querySelector('del')).toHaveTextContent('diez');
  });
});
