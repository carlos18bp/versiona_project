import { expect, test } from '../../test-with-coverage';
import { D3_OBSERVATIONS } from '../../helpers/flow-tags';
import { openSeededProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.describe('D3 — Observaciones ancladas', () => {
  test.slow();

  test(
    'D3-F01/F02/F04 — ancla, hilo, re-anclaje en v2 y resolución (I14)',
    { tag: [...D3_OBSERVATIONS, '@scenario:d3-f01', '@scenario:d3-f02', '@scenario:d3-f04'] },
    async ({ browser }) => {
      // Editor sube v1
      const editorContext = await browser.newContext({ storageState: 'e2e/.auth/editor.json' });
      const editorPage = await editorContext.newPage();
      await openSeededProject(editorPage);
      const title = uniqueName('Contrato D3');
      await uploadPdf(editorPage, 'contrato_v1.pdf', { title, message: 'v1' });
      const documentLink = editorPage
        .getByTestId('documents-list')
        .getByRole('link', { name: title });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(editorPage.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });
      const timelineUrl = editorPage.url();
      await editorPage.getByRole('link', { name: 'Ver documento' }).click();
      await editorPage.waitForURL(/versions\//);
      const v1Url = editorPage.url();

      // Revisor ancla una observación a §3 (D3-F01)
      const reviewerContext = await browser.newContext({
        storageState: 'e2e/.auth/reviewer.json',
      });
      const reviewerPage = await reviewerContext.newPage();
      await reviewerPage.goto(v1Url);
      await expect(reviewerPage.getByTestId('observations-panel')).toBeVisible({
        timeout: 20_000,
      });
      await reviewerPage.getByTestId('add-observation').click();
      await reviewerPage
        .getByTestId('observation-section')
        .selectOption({ label: '3. OBLIGACIONES DEL CONTRATISTA' });
      await reviewerPage
        .getByTestId('observation-body')
        .fill('La multa del 2% parece baja para la cuantía del contrato.');
      await reviewerPage.getByTestId('observation-submit').click();
      await expect(reviewerPage.getByText('Abierta')).toBeVisible({ timeout: 20_000 });
      await expect(reviewerPage.getByText(/Ancla exacta/)).toBeVisible();

      // El editor responde: open → answered (D3-F02, I14)
      await editorPage.reload();
      const replyInput = editorPage.locator('[data-testid^="reply-input-"]');
      await expect(replyInput).toBeVisible({ timeout: 20_000 });
      await replyInput.fill('Subimos la multa al 5% en la siguiente entrega.');
      await editorPage.locator('[data-testid^="reply-send-"]').click();
      await expect(editorPage.getByText('Respondida')).toBeVisible({ timeout: 20_000 });

      // Editor sube v2 (cambia §3) — el ancla se re-ancla (D3-F04)
      await editorPage.goto(timelineUrl);
      await uploadPdf(editorPage, 'contrato_v2.pdf', { message: 'v2 sube multa a 5%' });
      await expect(editorPage.getByTestId('version-item-2')).toBeVisible({ timeout: 90_000 });
      await editorPage
        .getByTestId('version-item-2')
        .getByRole('link', { name: 'Ver documento' })
        .click();
      await editorPage.waitForURL(/versions\//);
      const v2Url = editorPage.url();
      await expect(editorPage.getByText(/Re-anclada/)).toBeVisible({ timeout: 20_000 });

      // El revisor verifica la subsanación en v2 y resuelve (answered → resolved)
      await reviewerPage.goto(v2Url);
      await expect(reviewerPage.getByTestId('observations-panel')).toBeVisible({
        timeout: 20_000,
      });
      await reviewerPage.locator('[data-testid^="resolve-"]').click();
      // El hilo resuelto se oculta del listado por defecto: el filtro lo revela
      await reviewerPage.getByTestId('show-resolved').check();
      await expect(reviewerPage.getByText(/resuelta en v2/)).toBeVisible({ timeout: 20_000 });
      await expect(reviewerPage.getByText('Resuelta', { exact: true })).toBeVisible();

      await editorContext.close();
      await reviewerContext.close();
    }
  );
});
