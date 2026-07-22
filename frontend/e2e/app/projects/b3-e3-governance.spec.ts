import { expect, test } from '../../test-with-coverage';
import { B3_PROJECT_SETTINGS, E3_CHECKS } from '../../helpers/flow-tags';
import { openSeededProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.describe('B3 + E3 — Gobernanza del proyecto', () => {
  test.slow();

  test(
    'B3-F01/E3-F01 — el admin configura la checklist y la siguiente versión la evalúa con evidencia',
    {
      tag: [
        ...B3_PROJECT_SETTINGS,
        '@scenario:b3-f01',
        '@scenario:e3-f01',
        '@scenario:e3-f02',
      ],
    },
    async ({ browser }) => {
      // Admin: configura un check de texto requerido (crea config nueva — I8)
      const adminContext = await browser.newContext({ storageState: 'e2e/.auth/admin.json' });
      const adminPage = await adminContext.newPage();
      await openSeededProject(adminPage);
      await adminPage.getByTestId('project-settings-link').click();
      await adminPage.waitForURL(/\/settings$/);
      await expect(adminPage.getByTestId('project-config')).toBeVisible({ timeout: 20_000 });

      const checkRows = adminPage.locator('[data-testid^="check-label-"]');
      const initialCount = await checkRows.count();
      await adminPage.getByTestId('add-check').click();
      await expect(checkRows).toHaveCount(initialCount + 1);
      const index = initialCount;
      await adminPage.getByTestId(`check-label-${index}`).fill('Regula el anticipo');
      await adminPage.getByTestId(`check-type-${index}`).selectOption('required_text');
      await adminPage.getByTestId(`check-param-${index}`).fill('anticipo');
      await adminPage.getByTestId('save-config').click();
      await expect(adminPage.getByText(/Configuración v\d+ creada/)).toBeVisible({
        timeout: 15_000,
      });

      // Editor: sube un documento NUEVO — pina la config nueva y corre el check
      const editorContext = await browser.newContext({ storageState: 'e2e/.auth/editor.json' });
      const editorPage = await editorContext.newPage();
      await openSeededProject(editorPage);
      const title = uniqueName('Chequeado E3');
      await uploadPdf(editorPage, 'contrato_v1.pdf', { title, message: 'v1' });
      const documentLink = editorPage
        .getByTestId('documents-list')
        .getByRole('link', { name: title });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(editorPage.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });

      // Semáforo en el timeline (E3-F03)
      await expect(editorPage.getByTestId('check-light-1')).toBeVisible({ timeout: 15_000 });

      // ChecksPanel con evidencia (E3-F02)
      await editorPage.getByRole('link', { name: 'Ver documento' }).click();
      await editorPage.waitForURL(/versions\//);
      await expect(editorPage.getByTestId('checks-panel')).toBeVisible({ timeout: 20_000 });
      const anticipoCheck = editorPage
        .locator('[data-testid^="check-"][data-outcome]')
        .filter({ hasText: 'Regula el anticipo' })
        .first();
      await expect(anticipoCheck).toHaveAttribute('data-outcome', 'pass');
      await expect(anticipoCheck).toContainText('valor-y-forma-de-pago');

      await adminContext.close();
      await editorContext.close();
    }
  );

  test(
    'B3-P02 — la configuración está oculta para quien no es admin',
    { tag: [...E3_CHECKS, '@scenario:b3-p02'] },
    async ({ browser }) => {
      const viewerContext = await browser.newContext({ storageState: 'e2e/.auth/viewer.json' });
      const viewerPage = await viewerContext.newPage();
      await openSeededProject(viewerPage);
      await viewerPage.getByTestId('project-settings-link').click();
      await viewerPage.waitForURL(/\/settings$/);

      await expect(
        viewerPage.getByText('La configuración del proyecto es una vista de administración.')
      ).toBeVisible({ timeout: 20_000 });
      await expect(viewerPage.getByTestId('project-config')).toHaveCount(0);
      await viewerContext.close();
    }
  );
});
