import { expect, test } from '../../test-with-coverage';
import { C4_DELETE_DRAFT } from '../../helpers/flow-tags';
import { createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('C4 — Eliminar una versión borrador', () => {
  test(
    'C4-F01/F02 — a la papelera con doble confirmación, tombstone y restauración',
    { tag: [...C4_DELETE_DRAFT, '@scenario:c4-f01', '@scenario:c4-f02', '@outcome:success'] },
    async ({ page, browser }) => {
      // The title must be unique per run: /org/trash lists every trashed item in
      // the org with no project scope, so a run that dies between trashing v2 and
      // restoring it leaves an orphan row. With a fixed title the next run's
      // `Borrable · v2` matcher then resolves to two elements and C4-F01 goes red
      // permanently, until someone cleans the database by hand. Measured 2026-08-02.
      const docTitle = uniqueName('Borrable');
      await createProject(page, uniqueName('Papelera'));
      await uploadPdf(page, 'contrato_v1.pdf', { title: docTitle, message: 'v1' });
      await expect(page.getByText(docTitle)).toBeVisible({ timeout: 60_000 });
      await page.getByText(docTitle).click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 15_000 });
      await uploadPdf(page, 'contrato_v2.pdf', { message: 'v2 borrador' });
      await expect(page.getByTestId('version-item-2')).toBeVisible({ timeout: 60_000 });

      // Dos pasos: el botón exige escribir "v2" exacto
      await page.getByTestId('trash-version-2').click();
      await expect(page.getByTestId('type-to-confirm-submit')).toBeDisabled();
      await page.getByTestId('type-to-confirm-input').fill('v2');
      await page.getByTestId('type-to-confirm-submit').click();

      // Tombstone en el timeline (C4-F01)
      await expect(page.getByText(/v2 — versión eliminada/)).toBeVisible({ timeout: 15_000 });

      // La papelera de la org la lista y permite restaurar (owner)
      const ownerContext = await browser.newContext({ storageState: 'e2e/.auth/owner.json' });
      const ownerPage = await ownerContext.newPage();
      await ownerPage.goto('/org/trash');
      await expect(ownerPage.getByTestId('trash-list')).toBeVisible({ timeout: 15_000 });
      // Scoped to THIS document's row, not `.first()`: the trash is org-wide, so
      // the first row is whatever another spec trashed most recently.
      const trashedRow = ownerPage
        .getByTestId('trash-list')
        .locator('li')
        .filter({ hasText: `${docTitle} · v2` });
      await expect(trashedRow).toBeVisible();
      await trashedRow.getByTestId('restore-version').click();
      await expect(ownerPage.getByText('Elemento restaurado')).toBeVisible({ timeout: 10_000 });
      await ownerContext.close();

      // El timeline vuelve a mostrar v2 viva (C4-F02)
      await page.reload();
      await expect(page.getByText('v2 borrador')).toBeVisible({ timeout: 15_000 });
    }
  );

  test(
    'C4-E02 — una versión antigua (no la última) no puede eliminarse',
    { tag: [...C4_DELETE_DRAFT, '@scenario:c4-e02', '@outcome:error'] },
    async ({ page }) => {
      // Two guarantees at once: the backend refuses to trash a non-latest
      // version, AND the UI actually tells the user so. The refusal used to be
      // silent — `VersionTimeline`'s onConfirm had no failure branch, so the
      // dialog just closed — which is why this test also pins the toast.
      await createProject(page, uniqueName('Papelera Vieja'));
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'No borrable', message: 'v1' });
      await expect(page.getByText('No borrable')).toBeVisible({ timeout: 60_000 });
      await page.getByText('No borrable').click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 15_000 });
      await uploadPdf(page, 'contrato_v2.pdf', { message: 'v2 vigente' });
      await expect(page.getByTestId('version-item-2')).toBeVisible({ timeout: 60_000 });

      // v1 sigue mostrando su botón de papelera aunque ya no sea la última
      // (`is_draft` no distingue "es la última versión del documento").
      await page.getByTestId('trash-version-1').click();
      await expect(page.getByTestId('type-to-confirm-submit')).toBeDisabled();
      await page.getByTestId('type-to-confirm-input').fill('v1');
      await page.getByTestId('type-to-confirm-submit').click();

      // El rechazo se le dice al usuario: el mensaje del backend llega al
      // toaster en vez de cerrarse el diálogo en silencio.
      await expect(page.getByTestId('toaster')).toContainText(
        'Solo la última versión del documento puede eliminarse.',
        { timeout: 15_000 }
      );

      // Y v1 sigue viva, sin tombstone. La recarga obliga a releer el estado
      // del servidor, porque en el camino de fallo el timeline nunca se
      // refresca solo.
      await page.reload();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });

      // Positiva: v1 conserva su affordance de borrado, que sólo se renderiza
      // cuando la versión existe y NO está en la papelera. Sin esto, un borrado
      // duro (v1 desaparece del timeline) dejaría verdes a las negativas.
      await expect(page.getByTestId('trash-version-1')).toBeVisible();
      await expect(page.getByTestId('version-item-1')).not.toContainText('versión eliminada');
      await expect(page.getByText('v1 — versión eliminada')).toHaveCount(0);
    }
  );
});
