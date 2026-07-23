import { expect, test } from '../../test-with-coverage';
import { F3_ORG_AUDIT } from '../../helpers/flow-tags';

test.describe('F3 — Auditoría de la organización', () => {
  test(
    'F3-F01 — el admin ve los filtros y el export CSV',
    { tag: [...F3_ORG_AUDIT, '@scenario:f3-f01'] },
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
      await adminContext.close();
    }
  );

  test(
    'F3-P01 — quien no es admin ve el aviso de vista de administración',
    { tag: [...F3_ORG_AUDIT, '@scenario:f3-p01'] },
    async ({ browser }) => {
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
