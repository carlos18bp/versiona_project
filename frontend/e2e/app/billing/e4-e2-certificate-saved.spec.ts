import { expect, test } from '../../test-with-coverage';
import { E2_SAVED_COMPARISONS, E4_CONSTANCIA } from '../../helpers/flow-tags';
import { openSeededProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('E4 + E2 — Constancia exportable y comparaciones guardadas', () => {
  test.slow();

  test(
    'E4-F01 — sellar → aprobar → emitir constancia → PDF descargable',
    { tag: [...E4_CONSTANCIA, '@scenario:e4-f01', '@scenario:e4-f04'] },
    async ({ browser }) => {
      // Editor sube; revisor sella todo (aprueba); admin emite
      const editorContext = await browser.newContext({ storageState: 'e2e/.auth/editor.json' });
      const editorPage = await editorContext.newPage();
      await openSeededProject(editorPage);
      const title = uniqueName('Certificable');
      await uploadPdf(editorPage, 'contrato_v1.pdf', { title, message: 'v1' });
      const documentLink = editorPage
        .getByTestId('documents-list')
        .getByRole('link', { name: title });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(editorPage.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });
      await editorPage.getByRole('link', { name: 'Ver documento' }).click();
      await editorPage.waitForURL(/versions\//);
      const versionUrl = editorPage.url();

      const reviewerContext = await browser.newContext({
        storageState: 'e2e/.auth/reviewer.json',
      });
      const reviewerPage = await reviewerContext.newPage();
      await reviewerPage.goto(versionUrl);
      await expect(reviewerPage.getByTestId('seal-action-bar')).toBeVisible({ timeout: 20_000 });
      await reviewerPage.getByTestId('seal-all').click();
      await expect(
        reviewerPage.getByTestId('seal-reviewer@versiona.test')
      ).toBeVisible({ timeout: 20_000 });

      // Admin: la versión aprobada ofrece emitir constancia
      const adminContext = await browser.newContext({ storageState: 'e2e/.auth/admin.json' });
      const adminPage = await adminContext.newPage();
      await adminPage.goto(versionUrl);
      await expect(adminPage.getByTestId('certificate-panel')).toBeVisible({ timeout: 20_000 });

      const [popup] = await Promise.all([
        adminPage.waitForEvent('popup', { timeout: 30_000 }),
        adminPage.getByTestId('issue-certificate').click(),
      ]);
      await popup.close();

      // Verificación determinista del binario: API + URL firmada
      const versionId = versionUrl.split('/versions/')[1].split(/[/?#]/)[0];
      const access = (await adminContext.cookies()).find(
        (cookie) => cookie.name === 'access_token'
      )!.value;
      const listResponse = await adminPage.request.get(
        `http://127.0.0.1:8000/api/versions/${versionId}/certificates/`,
        { headers: { Authorization: `Bearer ${access}` } }
      );
      const certificates = (await listResponse.json()).results;
      expect(certificates.length).toBeGreaterThan(0);
      expect(certificates[0].serial).toMatch(/-\d{4}$/);

      const downloadResponse = await adminPage.request.get(
        `http://127.0.0.1:8000/api/versions/${versionId}/certificates/${certificates[0].public_id}/download/`,
        { headers: { Authorization: `Bearer ${access}` } }
      );
      const { url, snapshot } = await downloadResponse.json();
      expect(snapshot.seals[0].signature_valid_now).toBe(true);
      const pdfResponse = await adminPage.request.get(url);
      const body = await pdfResponse.body();
      expect(body.subarray(0, 4).toString()).toBe('%PDF');

      await editorContext.close();
      await reviewerContext.close();
      await adminContext.close();
    }
  );

  test(
    'E2-F01 — guardar una comparación con nombre y reabrirla desde el proyecto',
    { tag: [...E2_SAVED_COMPARISONS, '@scenario:e2-f01'] },
    async ({ page }) => {
      await openSeededProject(page);
      const title = uniqueName('Comparable');
      await uploadPdf(page, 'contrato_v1.pdf', { title, message: 'v1' });
      const documentLink = page
        .getByTestId('documents-list')
        .getByRole('link', { name: title });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });
      await uploadPdf(page, 'contrato_v2.pdf', { message: 'v2' });
      await expect(page.getByTestId('version-item-2')).toBeVisible({ timeout: 90_000 });

      await page.getByTestId('select-version-1').check();
      await page.getByTestId('select-version-2').check();
      await page.getByTestId('compare-selected').click();
      await page.waitForURL(/\/compare\//, { timeout: 20_000 });
      await expect(page.getByTestId('compare-view')).toBeVisible({ timeout: 30_000 });

      const savedName = uniqueName('Entrega');
      page.once('dialog', (dialog) => void dialog.accept(savedName));
      await page.getByTestId('save-comparison').click();
      await expect(page.getByText('Comparación guardada')).toBeVisible({ timeout: 15_000 });

      // La lista del proyecto la ofrece con su enlace profundo
      await openSeededProject(page);
      const savedRow = page.getByTestId(`saved-${savedName}`);
      await expect(savedRow).toBeVisible({ timeout: 15_000 });
      await savedRow.click();
      await page.waitForURL(/\/compare\//, { timeout: 20_000 });
      await expect(page.getByTestId('compare-view')).toBeVisible({ timeout: 30_000 });
    }
  );
});
