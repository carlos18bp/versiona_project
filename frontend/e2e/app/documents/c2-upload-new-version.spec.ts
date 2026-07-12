import { expect, test } from '../../test-with-coverage';
import { C2_UPLOAD_VERSION } from '../../helpers/flow-tags';
import { createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('C2 — Subir una nueva versión', () => {
  // Three real upload+analysis cycles (MinIO + PyMuPDF) in one journey.
  test.slow();

  test(
    'C2-F01 — la re-entrega crea v2 con su mensaje y análisis automático',
    { tag: [...C2_UPLOAD_VERSION, '@scenario:c2-f01', '@scenario:c2-e01', '@scenario:c2-a01'] },
    async ({ page }) => {
      await createProject(page, uniqueName('Reentregas'));
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'Contrato R', message: 'v1' });

      const documentLink = page
        .getByTestId('documents-list')
        .getByRole('link', { name: /Contrato R/ });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });

      // v2 con mensaje (el commit)
      await uploadPdf(page, 'contrato_v2.pdf', { message: 'atiende observaciones' });
      await expect(page.getByTestId('version-item-2')).toBeVisible({ timeout: 90_000 });
      await expect(page.getByText('atiende observaciones')).toBeVisible();

      // C2-E01: el binario idéntico a v2 se rechaza
      await uploadPdf(page, 'contrato_v2.pdf', { message: 'duplicado' });
      await expect(page.getByTestId('upload-error')).toContainText('idéntico a la versión v2');
      await page.getByRole('button', { name: 'Cancelar' }).click();

      // C2-A01: el mensaje del borrador es editable (I2b)
      await page.getByTestId('edit-message-2').click();
      await page.getByTestId('edit-message-input').fill('mensaje corregido');
      await page.getByRole('button', { name: 'Guardar' }).click();
      await expect(page.getByText('mensaje corregido')).toBeVisible({ timeout: 15_000 });
    }
  );
});
