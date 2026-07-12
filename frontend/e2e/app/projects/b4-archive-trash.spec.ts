import { expect, test } from '../../test-with-coverage';
import { B4_ARCHIVE_DELETE } from '../../helpers/flow-tags';
import { createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('B4 — Archivar y eliminar proyecto', () => {
  test.slow();

  test(
    'B4-F01/F02 — archivar bloquea escritura; papelera con nombre exacto y restauración',
    { tag: [...B4_ARCHIVE_DELETE, '@scenario:b4-f01', '@scenario:b4-f02'] },
    async ({ page, browser }) => {
      const name = uniqueName('Efímero');
      await createProject(page, name);
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'Doc B4', message: 'v1' });
      await expect(
        page.getByTestId('documents-list').getByRole('link', { name: 'Doc B4' })
      ).toBeVisible({ timeout: 90_000 });

      // Archivar → banner de solo lectura (B4-F01/L01)
      await page.getByTestId('archive-project').click();
      await expect(page.getByTestId('archived-banner')).toBeVisible({ timeout: 15_000 });

      // Desarchivar y eliminar con confirmación de nombre exacto (B4-F02)
      await page.getByTestId('archive-project').click();
      await expect(page.getByTestId('archived-banner')).toHaveCount(0, { timeout: 15_000 });
      await page.getByTestId('trash-project').click();
      await expect(page.getByTestId('type-to-confirm-submit')).toBeDisabled();
      await page.getByTestId('type-to-confirm-input').fill(name);
      await page.getByTestId('type-to-confirm-submit').click();
      await page.waitForURL(/\/projects$/, { timeout: 20_000 });

      // Ya no aparece en el tablero
      await page.getByTestId('board-search').fill(name);
      await expect(page.getByTestId('projects-grid')).toHaveCount(0, { timeout: 15_000 });

      // La papelera de la org lo lista y lo restaura (owner)
      const ownerContext = await browser.newContext({ storageState: 'e2e/.auth/owner.json' });
      const ownerPage = await ownerContext.newPage();
      await ownerPage.goto('/org/trash');
      await expect(ownerPage.getByTestId('trash-list')).toBeVisible({ timeout: 20_000 });
      await expect(ownerPage.getByText(name)).toBeVisible();
      await ownerPage
        .getByTestId('trash-list')
        .locator('li', { hasText: name })
        .getByTestId('restore-project')
        .click();
      await expect(ownerPage.getByText('Elemento restaurado')).toBeVisible({ timeout: 15_000 });
      await ownerContext.close();

      // De vuelta en el tablero del editor (recarga: la búsqueda anterior
      // quedó con el mismo texto y un fill idéntico no re-dispara el fetch)
      await page.goto('/projects');
      await page.getByTestId('board-search').fill(name);
      await expect(
        page.getByTestId('projects-grid').getByRole('link', { name })
      ).toBeVisible({ timeout: 15_000 });
    }
  );
});
