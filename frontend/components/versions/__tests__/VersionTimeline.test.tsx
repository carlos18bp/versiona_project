import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { VersionTimeline } from '../VersionTimeline';
import type { VersionSummary } from '../../../lib/types';

const editMessage = jest.fn();
const trashVersion = jest.fn();
const downloadUrl = jest.fn();

jest.mock('../../../lib/stores/versionStore', () => ({
  useVersionStore: (selector: (s: Record<string, unknown>) => unknown) =>
    selector({ editMessage, trashVersion, downloadUrl }),
}));

function makeVersion(overrides: Partial<VersionSummary> = {}): VersionSummary {
  return {
    public_id: 'v1',
    number: 1,
    message: 'primera entrega',
    sha256: 'a'.repeat(64),
    size_bytes: 1000,
    page_count: 2,
    source_scenario: 'text_native',
    analysis_status: 'ready',
    error_detail: '',
    is_approved: false,
    is_draft: true,
    is_trashed: false,
    author_email: 'editor@versiona.test',
    thumb_url: null,
    created_at: '2026-07-12T10:00:00Z',
    ...overrides,
  };
}

describe('VersionTimeline', () => {
  beforeEach(() => {
    editMessage.mockReset();
    trashVersion.mockReset();
  });

  it('[C3-F01] renders author, message and analysis badge per version', () => {
    render(
      <VersionTimeline
        projectId="p"
        documentId="d"
        versions={[makeVersion()]}
        canEdit
        onChanged={jest.fn()}
      />
    );

    expect(screen.getByText('v1')).toBeInTheDocument();
    expect(screen.getByText(/primera entrega/)).toBeInTheDocument();
    expect(screen.getByText(/editor@versiona.test/)).toBeInTheDocument();
    expect(screen.getByText('Versión lista')).toBeInTheDocument();
  });

  it('[C4-F01-ui] shows a tombstone for a trashed version', () => {
    render(
      <VersionTimeline
        projectId="p"
        documentId="d"
        versions={[makeVersion({ is_trashed: true, number: 3, public_id: 'v3' })]}
        canEdit
        onChanged={jest.fn()}
      />
    );

    expect(screen.getByText(/v3 — versión eliminada/)).toBeInTheDocument();
  });

  it('[C2-E02-ui] hides message editing when the version is not a draft', () => {
    render(
      <VersionTimeline
        projectId="p"
        documentId="d"
        versions={[makeVersion({ is_draft: false, is_approved: true })]}
        canEdit
        onChanged={jest.fn()}
      />
    );

    expect(screen.queryByTestId('edit-message-1')).not.toBeInTheDocument();
    expect(screen.getByText('Aprobada')).toBeInTheDocument();
  });

  it('[C2-A01-ui] edits a draft message inline', async () => {
    editMessage.mockResolvedValue(true);
    const onChanged = jest.fn();
    render(
      <VersionTimeline
        projectId="p"
        documentId="d"
        versions={[makeVersion()]}
        canEdit
        onChanged={onChanged}
      />
    );

    await userEvent.click(screen.getByTestId('edit-message-1'));
    const input = screen.getByTestId('edit-message-input');
    await userEvent.clear(input);
    await userEvent.type(input, 'mensaje corregido');
    await userEvent.click(screen.getByRole('button', { name: 'Guardar' }));

    expect(editMessage).toHaveBeenCalledWith('v1', 'mensaje corregido');
    expect(onChanged).toHaveBeenCalled();
  });

  it('[C4-F01-2p] trashing requires typing the exact version tag', async () => {
    trashVersion.mockResolvedValue(true);
    render(
      <VersionTimeline
        projectId="p"
        documentId="d"
        versions={[makeVersion()]}
        canEdit
        onChanged={jest.fn()}
      />
    );

    await userEvent.click(screen.getByTestId('trash-version-1'));
    const submit = screen.getByTestId('type-to-confirm-submit');
    expect(submit).toBeDisabled();

    await userEvent.type(screen.getByTestId('type-to-confirm-input'), 'v1');
    expect(submit).toBeEnabled();

    await userEvent.click(submit);
    expect(trashVersion).toHaveBeenCalledWith('v1');
  });
});
