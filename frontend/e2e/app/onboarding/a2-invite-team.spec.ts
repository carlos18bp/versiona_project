import { expect, test } from '../../test-with-coverage';
import { A2_INVITE_TEAM } from '../../helpers/flow-tags';
import { waitForEmail } from '../../helpers/mailpit';
import { openSeededProject, uniqueEmail } from '../../helpers/versiona';

test.describe('A2 — Invitar al equipo', () => {
  test.slow();

  test(
    'A2-F01/F02 — invitación por email, registro y aterrizaje directo en el proyecto',
    { tag: [...A2_INVITE_TEAM, '@scenario:a2-f01', '@scenario:a2-f02', '@outcome:success'] },
    async ({ browser }) => {
      const invitee = uniqueEmail('inv');

      // Admin invita desde la configuración del proyecto
      const adminContext = await browser.newContext({ storageState: 'e2e/.auth/admin.json' });
      const adminPage = await adminContext.newPage();
      await openSeededProject(adminPage);
      await adminPage.getByTestId('project-settings-link').click();
      await adminPage.waitForURL(/\/settings$/);
      await expect(adminPage.getByTestId('members-section')).toBeVisible({ timeout: 20_000 });
      await adminPage.getByTestId('invite-email').fill(invitee);
      await adminPage.getByTestId('invite-role').selectOption('reviewer');
      await adminPage.getByTestId('send-invite').click();
      await expect(
        adminPage.getByTestId('invitations-list').getByText(invitee)
      ).toBeVisible({ timeout: 15_000 });

      // El email llega con el enlace del token
      const email = await waitForEmail({ to: invitee, subjectContains: 'invitó' });
      expect(email.Subject).toContain('Torre E2E');

      // La invitada abre el enlace SIN sesión: la landing pública la guía
      const inviteeContext = await browser.newContext();
      const inviteePage = await inviteeContext.newPage();
      // El token viaja en el cuerpo del email; lo recuperamos vía API pública
      const adminApi = await adminContext.request.get(
        'http://127.0.0.1:8025/api/v1/search?query=' + encodeURIComponent(`to:${invitee}`)
      );
      const messages = (await adminApi.json()).messages;
      const detail = await adminContext.request.get(
        `http://127.0.0.1:8025/api/v1/message/${messages[0].ID}`
      );
      const body = (await detail.json()).Text as string;
      const token = body.match(/\/invite\/([\w-]+)/)?.[1];
      expect(token).toMatch(/^[\w-]{20,64}$/);

      await inviteePage.goto(`/invite/${token}`);
      await expect(inviteePage.getByTestId('invite-landing')).toBeVisible({ timeout: 20_000 });
      await expect(inviteePage.getByText(/reviewer/)).toBeVisible();

      // Crea su cuenta con el email invitado y vuelve a aceptar
      await inviteePage
        .getByTestId('invite-landing')
        .getByRole('link', { name: 'Crear cuenta' })
        .click();
      await inviteePage.waitForURL(/sign-up/);
      await inviteePage.getByPlaceholder('Email').fill(invitee);
      await inviteePage.getByPlaceholder('Password', { exact: true }).fill('secreta123');
      await inviteePage.getByPlaceholder('Confirm password').fill('secreta123');
      await inviteePage.getByRole('button', { name: 'Crear cuenta' }).click();
      await inviteePage.waitForURL(/onboarding/, { timeout: 30_000 });

      await inviteePage.goto(`/invite/${token}`);
      await inviteePage.getByTestId('accept-invitation').click();

      // Aterriza directo en el proyecto (A2-F02)
      await inviteePage.waitForURL(/\/projects\/[0-9a-f-]+$/, { timeout: 20_000 });
      await expect(inviteePage.getByTestId('upload-dropzone')).toBeVisible({ timeout: 15_000 });

      await adminContext.close();
      await inviteeContext.close();
    }
  );

  // `storageState` scoped to this block only: a describe-level `test.use` also
  // becomes the default for every bare `browser.newContext()` in its scope,
  // which would silently authenticate F01's supposedly anonymous invitee.
  test.describe('con sesión de admin', () => {
    test.use({ storageState: 'e2e/.auth/admin.json' });

    test(
      'A2-E01 — invitar dos veces al mismo email no crea una invitación duplicada',
      { tag: [...A2_INVITE_TEAM, '@scenario:a2-e01', '@outcome:error'] },
      async ({ page }) => {
        // Catches: a regression that drops/weakens the duplicate-pending check
        // in `create_invitation`, or a frontend that stops surfacing
        // `err.response.data.error` and silently swallows the 409.
        const invitee = uniqueEmail('dup');

        await openSeededProject(page);
        await page.getByTestId('project-settings-link').click();
        await page.waitForURL(/\/settings$/);
        await expect(page.getByTestId('members-section')).toBeVisible({ timeout: 20_000 });

        await page.getByTestId('invite-email').fill(invitee);
        await page.getByTestId('send-invite').click();
        await expect(
          page.getByTestId('invitations-list').getByText(invitee)
        ).toBeVisible({ timeout: 15_000 });

        // Segundo envío al MISMO email: el backend rechaza el duplicado.
        await page.getByTestId('invite-email').fill(invitee);
        await page.getByTestId('send-invite').click();

        await expect(page.getByTestId('toaster')).toContainText(
          `Ya hay una invitación pendiente para ${invitee}.`,
          { timeout: 15_000 }
        );
        await expect(
          page.getByTestId('invitations-list').locator('li', { hasText: invitee })
        ).toHaveCount(1);
      }
    );
  });
});
