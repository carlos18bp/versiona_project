import { expect, test } from '../../test-with-coverage';
import { D1_REQUEST_REVIEW } from '../../helpers/flow-tags';
import { waitForEmail } from '../../helpers/mailpit';
import { openSeededProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.describe('D1 — Solicitar revisión (el pull request)', () => {
  test.slow();
  // F01 builds its own contexts via `browser` and never touches the default
  // `page`/`context` fixtures, so this admin storageState only affects tests
  // (like D1-E01 below) that actually request `page`.
  test.use({ storageState: 'e2e/.auth/admin.json' });

  test(
    'D1-F01/F03 — el editor asigna, el revisor recibe y su sello completa la revisión',
    { tag: [...D1_REQUEST_REVIEW, '@scenario:d1-f01', '@scenario:d1-f03', '@scenario:d1-f04', '@outcome:success'] },
    async ({ browser }) => {
      // Editor: documento nuevo y solicitud de revisión
      const editorContext = await browser.newContext({ storageState: 'e2e/.auth/editor.json' });
      const editorPage = await editorContext.newPage();
      await openSeededProject(editorPage);
      const title = uniqueName('Contrato D1');
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

      await editorPage.getByTestId('request-review').click();
      await editorPage.getByTestId('pick-reviewer-reviewer@versiona.test').check();
      await editorPage.getByTestId('review-message').fill('enfócate en las multas');
      await editorPage.getByTestId('send-review-request').click();
      await expect(
        editorPage.getByTestId('assignment-reviewer@versiona.test')
      ).toBeVisible({ timeout: 20_000 });
      await expect(editorPage.getByText('Pendiente de')).toBeVisible();

      // Revisor: la asignación llega a su inbox con el mensaje (y por email)
      const reviewerContext = await browser.newContext({
        storageState: 'e2e/.auth/reviewer.json',
      });
      const reviewerPage = await reviewerContext.newPage();
      await reviewerPage.goto('/inbox');
      const assignmentsBox = reviewerPage.getByTestId('inbox-assignments');
      await expect(assignmentsBox).toBeVisible({ timeout: 20_000 });
      await expect(assignmentsBox).toContainText(title);
      await expect(assignmentsBox).toContainText('enfócate en las multas');
      await waitForEmail({ to: 'reviewer@versiona.test', subjectContains: 'revisión' });

      // El sello del revisor completa su asignación y la solicitud (D1-F03)
      await reviewerPage.goto(versionUrl);
      await expect(reviewerPage.getByTestId('seal-action-bar')).toBeVisible({ timeout: 20_000 });
      await reviewerPage.getByTestId('seal-all').click();
      await expect(
        reviewerPage.getByTestId('seal-reviewer@versiona.test')
      ).toBeVisible({ timeout: 20_000 });

      await editorPage.reload();
      await expect(editorPage.getByText('Revisión completa')).toBeVisible({ timeout: 20_000 });

      await editorContext.close();
      await reviewerContext.close();
    }
  );

  test(
    'D1-E01 — un admin no puede asignarse su propia revisión',
    { tag: [...D1_REQUEST_REVIEW, '@scenario:d1-e01', '@outcome:error'] },
    async ({ page }) => {
      // Catches: dropping the self-assignment guard from
      // `create_review_request` would let a reviewer approve their own
      // upload, undermining the "second pair of eyes" premise of D1/D4.
      await openSeededProject(page);
      const title = uniqueName('Contrato D1 Auto');
      await uploadPdf(page, 'contrato_v1.pdf', { title, message: 'v1' });
      const documentLink = page
        .getByTestId('documents-list')
        .getByRole('link', { name: title });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });
      await page.getByRole('link', { name: 'Ver documento' }).click();
      await page.waitForURL(/versions\//);

      await page.getByTestId('request-review').click();
      await page.getByTestId('pick-reviewer-admin@versiona.test').check();
      await page.getByTestId('send-review-request').click();

      await expect(page.getByTestId('toaster')).toContainText(
        'No puedes asignarte tu propia revisión.',
        { timeout: 15_000 }
      );
      await expect(page.getByRole('dialog')).toBeVisible();
      await expect(page.getByTestId('request-review')).toBeVisible();
    }
  );
});
