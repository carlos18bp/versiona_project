import { expect, test } from '../../test-with-coverage';
import { D2_ASSISTED_REVIEW } from '../../helpers/flow-tags';
import { openSeededProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.describe('D2 — Revisar con asistencia', () => {
  test.slow();

  test(
    'D2-F01 — "ya revisado por ti" acota la re-revisión a lo que cambió',
    { tag: [...D2_ASSISTED_REVIEW, '@scenario:d2-f01', '@scenario:d2-l01'] },
    async ({ browser }) => {
      // Editor sube v1
      const editorContext = await browser.newContext({ storageState: 'e2e/.auth/editor.json' });
      const editorPage = await editorContext.newPage();
      await openSeededProject(editorPage);
      const title = uniqueName('Contrato D2');
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

      // Revisor sella §1–2 en v1 — SIN contexto todavía (D2-L01)
      const reviewerContext = await browser.newContext({
        storageState: 'e2e/.auth/reviewer.json',
      });
      const reviewerPage = await reviewerContext.newPage();
      await reviewerPage.goto(v1Url);
      await expect(reviewerPage.getByTestId('seal-action-bar')).toBeVisible({ timeout: 20_000 });
      await expect(reviewerPage.getByTestId('review-context-bar')).toHaveCount(0);
      await reviewerPage.getByTestId('seal-sections-open').click();
      await reviewerPage.getByTestId('pick-objeto-del-contrato').check();
      await reviewerPage.getByTestId('pick-definiciones').check();
      await reviewerPage.getByTestId('seal-picked').click();
      await expect(
        reviewerPage.getByTestId('seal-reviewer@versiona.test')
      ).toBeVisible({ timeout: 20_000 });

      // Editor sube v2 (cambia §3/§5, elimina §6)
      await editorPage.goto(timelineUrl);
      await uploadPdf(editorPage, 'contrato_v2.pdf', { message: 'v2' });
      await expect(editorPage.getByTestId('version-item-2')).toBeVisible({ timeout: 90_000 });
      await editorPage
        .getByTestId('version-item-2')
        .getByRole('link', { name: 'Ver documento' })
        .click();
      await editorPage.waitForURL(/versions\//);
      const v2Url = editorPage.url();

      // Revisor abre v2: el contexto D2 acota su trabajo
      await reviewerPage.goto(v2Url);
      const contextBar = reviewerPage.getByTestId('review-context-bar');
      await expect(contextBar).toBeVisible({ timeout: 20_000 });
      await expect(contextBar).toContainText('Sellaste la v1');
      // Lo que cambió está como chip clicable; lo intacto solo como conteo
      await expect(
        contextBar.getByTestId('context-changed-obligaciones-del-contratista')
      ).toBeVisible();
      await expect(contextBar).toContainText('Intactas desde tu sello');
      await expect(
        contextBar.getByTestId('context-changed-objeto-del-contrato')
      ).toHaveCount(0);

      await editorContext.close();
      await reviewerContext.close();
    }
  );
});
