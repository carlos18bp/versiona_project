import { expect, test } from '../../test-with-coverage';
import { C3_HISTORY } from '../../helpers/flow-tags';
import { createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('C3 — Navegar el historial', () => {
  test(
    'C3-F01/F02 — timeline con autor, mensaje y miniatura; descarga por URL firmada',
    { tag: [...C3_HISTORY, '@scenario:c3-f01', '@scenario:c3-f02', '@outcome:display'] },
    async ({ page }) => {
      await createProject(page, uniqueName('Historial'));
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'Contrato H', message: 'v1 inicial' });
      await expect(page.getByText('Contrato H')).toBeVisible({ timeout: 60_000 });
      await page.getByText('Contrato H').click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 15_000 });

      await uploadPdf(page, 'contrato_v2.pdf', { message: 'segunda entrega' });
      await expect(page.getByTestId('version-item-2')).toBeVisible({ timeout: 60_000 });

      // Autor y mensajes visibles por versión (C3-F01)
      await expect(page.getByText('editor@versiona.test').first()).toBeVisible();
      await expect(page.getByText('v1 inicial')).toBeVisible();
      await expect(page.getByText('segunda entrega')).toBeVisible();

      // Descarga: el endpoint entrega una URL firmada (C3-F02)
      const downloadResponse = page.waitForResponse(
        (response) => response.url().includes('/download/') && response.status() === 200
      );
      await page
        .getByTestId('version-item-2')
        .getByRole('button', { name: 'Descargar' })
        .click();
      const response = await downloadResponse;
      const body = await response.json();

      // Backend-agnostic, mirroring backend/documents/tests/views/
      // test_document_endpoints.py: what matters is that the URL is a *signed
      // capability* — it works as handed over and stops working once tampered
      // with. Asserting 'X-Amz-Signature' pinned the storage vendor rather than
      // the behaviour, so it went stale the moment the guarantee came from our
      // own signer instead of S3.
      // Status codes only, never the body: with OBJECT_STORAGE_SENDFILE_ROOT
      // set, delivery is handed to nginx via X-Accel-Redirect and Django
      // answers 200 with an empty body — asserting bytes would pass in CI and
      // fail on every host configured like staging.
      expect((await page.request.get(body.url)).status()).toBe(200);
      expect(
        (await page.request.get(body.url.replace('/api/objects/', '/api/objects/x'))).status()
      ).toBe(403);
    }
  );
});
