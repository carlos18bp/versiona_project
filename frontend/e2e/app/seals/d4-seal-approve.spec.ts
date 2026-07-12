import { expect, test } from '../../test-with-coverage';
import { D4_SEAL_APPROVE } from '../../helpers/flow-tags';
import { openSeededProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.describe('D4 — Aprobar con sello', () => {
  test.slow(); // real upload + analysis before sealing

  test(
    'D4-F01/F02 — el revisor sella el documento completo, la firma verifica y la versión queda aprobada',
    { tag: [...D4_SEAL_APPROVE, '@scenario:d4-f01', '@scenario:d4-f02'] },
    async ({ browser }) => {
      // Editor prepares the document
      const editorContext = await browser.newContext({ storageState: 'e2e/.auth/editor.json' });
      const editorPage = await editorContext.newPage();
      await openSeededProject(editorPage);
      const title = uniqueName('Contrato D4');
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

      // El editor NO ve la barra de sellado (oculto por rol)
      await expect(editorPage.getByTestId('seals-panel')).toBeVisible({ timeout: 20_000 });
      await expect(editorPage.getByTestId('seal-action-bar')).toHaveCount(0);

      // Reviewer seals the whole document
      const reviewerContext = await browser.newContext({
        storageState: 'e2e/.auth/reviewer.json',
      });
      const reviewerPage = await reviewerContext.newPage();
      await reviewerPage.goto(versionUrl);
      await expect(reviewerPage.getByTestId('seal-action-bar')).toBeVisible({ timeout: 20_000 });
      await reviewerPage.getByTestId('seal-all').click();

      // El sello aparece con su titular y la versión queda aprobada (I10)
      await expect(
        reviewerPage.getByTestId('seal-reviewer@versiona.test')
      ).toBeVisible({ timeout: 20_000 });
      await expect(
        reviewerPage.getByRole('heading', { level: 1 }).locator('..').getByText('Aprobada')
      ).toBeVisible({ timeout: 15_000 });

      // D4-F02: la firma Ed25519 verifica desde la UI
      await reviewerPage.getByTestId(/verify-/).click();
      await expect(
        reviewerPage.getByText(/Firma Ed25519 válida/)
      ).toBeVisible({ timeout: 15_000 });

      await editorContext.close();
      await reviewerContext.close();
    }
  );
});
