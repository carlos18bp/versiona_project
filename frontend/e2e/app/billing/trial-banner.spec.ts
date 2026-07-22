import { expect, test } from '../../test-with-coverage';
import { TRIAL_VISIBILITY } from '../../helpers/flow-tags';

/** It9 — la promesa del landing ("14 días de Pro incluidos") tiene prueba UI:
 * la cuenta fresca ve el banner del trial con los días restantes. */

test.describe('Trial — visibilidad del banner', () => {
  test.slow();

  test(
    'TRIAL-F01 — el registro fresco ve el banner Pro con días restantes y lo descarta por sesión',
    { tag: [...TRIAL_VISIBILITY, '@scenario:trial-f01'] },
    async ({ page }) => {
      const email = `trial-${Date.now().toString(36)}@versiona.test`;

      await page.goto('/sign-up');
      await page.getByPlaceholder('Email').fill(email);
      await page.getByPlaceholder('Password', { exact: true }).fill('secreta123');
      await page.getByPlaceholder('Confirm password').fill('secreta123');
      await page.getByRole('button', { name: 'Crear cuenta' }).click();
      await page.waitForURL(/onboarding/, { timeout: 30_000 });
      await page.getByTestId('onboarding-org-name').fill('Trialera SAS');
      await page.getByTestId('onboarding-submit').click();
      await page.waitForURL(/\/compare\//, { timeout: 120_000 });

      await expect(page.getByTestId('trial-banner')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByTestId('trial-banner')).toContainText(/Prueba Pro/);
      await expect(page.getByTestId('trial-banner')).toContainText(/1[0-4] días/);
      await expect(page.getByTestId('trial-banner-plans')).toHaveAttribute(
        'href',
        '/precios'
      );

      await page.getByTestId('trial-banner-dismiss').click();
      await expect(page.getByTestId('trial-banner')).toHaveCount(0);

      // El descarte persiste dentro de la sesión del navegador
      await page.goto('/projects');
      await expect(page.getByTestId('projects-grid')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByTestId('trial-banner')).toHaveCount(0);
    }
  );
});
