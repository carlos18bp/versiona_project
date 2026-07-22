import { expect, test } from '../../test-with-coverage';
import { A2_INVITE_TEAM } from '../../helpers/flow-tags';
import { waitForEmail } from '../../helpers/mailpit';
import { openSeededProject } from '../../helpers/versiona';

test.describe('A2 — Invitar al equipo', () => {
  test.slow();

  test(
    'A2-F01/F02 — invitación por email, registro y aterrizaje directo en el proyecto',
    { tag: [...A2_INVITE_TEAM, '@scenario:a2-f01', '@scenario:a2-f02'] },
    async ({ browser }) => {
      const invitee = `inv-${Date.now().toString(36)}@versiona.test`;

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
      expect(token).toBeTruthy();

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
});
