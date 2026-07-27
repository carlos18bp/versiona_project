import { expect, test } from '../../test-with-coverage';
import { F3_ORG_AUDIT } from '../../helpers/flow-tags';

test.describe('F3 — Auditoría de la organización', () => {
  test(
    'F3-F01 — el admin ve los filtros, filtra por tipo y el export CSV',
    { tag: [...F3_ORG_AUDIT, '@scenario:f3-f01', '@outcome:display'] },
    async ({ browser }) => {
      const adminContext = await browser.newContext({ storageState: 'e2e/.auth/admin.json' });
      const adminPage = await adminContext.newPage();

      await adminPage.goto('/org/audit');

      await expect(adminPage.getByTestId('filter-type')).toBeVisible({ timeout: 20_000 });
      await expect(adminPage.getByTestId('filter-actor')).toBeVisible();
      await expect(adminPage.getByTestId('apply-filters')).toBeVisible();
      await expect(adminPage.getByTestId('export-csv')).toHaveAttribute(
        'href',
        /\/audit\/\?export=csv/
      );

      // filter-type es un <input> de texto, no un <select>: el backend
      // matchea event_type de forma exacta. Un tipo inexistente no matchea
      // nada, y el AsyncBoundary del listado renderiza el EmptyState en vez
      // de audit-list — la lista queda vacía por completo, no en "0 filas".
      await adminPage.getByTestId('filter-type').fill('e2e-f3f01-no-such-event-type');
      await adminPage.getByTestId('apply-filters').click();
      await expect(adminPage.getByTestId('audit-list')).toHaveCount(0, { timeout: 20_000 });

      await adminContext.close();
    }
  );

  test(
    'F3-P01 — quien no es admin ve el aviso de vista de administración',
    { tag: [...F3_ORG_AUDIT, '@scenario:f3-p01', '@outcome:failure'] },
    async ({ browser }) => {
      // quality: allow-no-interaction (permission gate renders on navigation; the restricted-notice IS the outcome)
      const viewerContext = await browser.newContext({ storageState: 'e2e/.auth/viewer.json' });
      const viewerPage = await viewerContext.newPage();

      await viewerPage.goto('/org/audit');

      await expect(
        viewerPage.getByText('La auditoría es una vista de administración de la organización.')
      ).toBeVisible({ timeout: 20_000 });
      await viewerContext.close();
    }
  );
});
