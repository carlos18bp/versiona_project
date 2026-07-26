import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import OrgAuditPage from '../audit/page';
import { api } from '../../../lib/services/http';

jest.mock('../../../lib/services/http', () => ({ api: { get: jest.fn() } }));
jest.mock('../../../lib/hooks/useRequireAuth', () => ({
  useRequireAuth: () => ({ isAuthenticated: true }),
}));
jest.mock('../../../lib/stores/orgStore', () => {
  const state = { activeOrgId: 'org-1', fetchOrgs: jest.fn(), orgs: [] };
  return { useOrgStore: (selector: (s: typeof state) => unknown) => selector(state) };
});

const mockGet = api.get as jest.Mock;

const auditRow = {
  event_type: 'member.invited',
  actor_email: 'owner@versiona.test',
  payload: {},
  created_at: '2026-07-20T10:00:00Z',
};

describe('OrgAuditPage (F3)', () => {
  beforeEach(() => mockGet.mockReset());

  // Falla si buildQuery pierde/renombra la key `type` (typo de param) o si el
  // onSubmit del filtro dispara load() con un closure viejo de `filters`
  // (stale state): en ambos casos la 2da llamada NO llevaría `type=member.invited`,
  // y org_audit (backend), que sólo lee request.query_params.get('type'), lo
  // ignoraría en silencio devolviendo la lista sin filtrar.
  it('[F3-F02] applying the type filter re-fetches the audit log scoped to that type', async () => {
    mockGet.mockResolvedValue({ data: { results: [auditRow] } });

    render(<OrgAuditPage />);

    await screen.findByTestId('audit-list');
    expect(mockGet).toHaveBeenCalledTimes(1);

    await userEvent.type(screen.getByTestId('filter-type'), 'member.invited');
    await userEvent.click(screen.getByTestId('apply-filters'));

    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(2));
    expect(mockGet).toHaveBeenLastCalledWith('orgs/org-1/audit/?type=member.invited');
  });
});
