import { expect, test } from '../../test-with-coverage';
import { F1_BILLING, F2_USAGE_PANEL } from '../../helpers/flow-tags';

/** F1+F2 sobre una cuenta FRESCA (plan free): el ejemplo del onboarding llena
 * el cupo de 1 proyecto; el segundo golpea el límite con CTA informativo. */

test.describe('F1+F2 — Límites del plan y consumo', () => {
  test.slow();

  test(
    'F1-L01/F2-F01 — el límite bloquea con CTA y el panel avisa la capacidad',
    { tag: [...F1_BILLING, ...F2_USAGE_PANEL, '@scenario:f1-l01', '@scenario:f2-f01'] },
    async ({ page }) => {
      const email = `free-${Date.now().toString(36)}@versiona.test`;

      // Registro + onboarding (siembra el proyecto ejemplo ⇒ 1/1 activo)
      await page.goto('/sign-up');
      await page.getByPlaceholder('Email').fill(email);
      await page.getByPlaceholder('Password', { exact: true }).fill('secreta123');
      await page.getByPlaceholder('Confirm password').fill('secreta123');
      await page.getByRole('button', { name: 'Crear cuenta' }).click();
      await page.waitForURL(/onboarding/, { timeout: 30_000 });
      await page.getByTestId('onboarding-org-name').fill('Limitada SAS');
      await page.getByTestId('onboarding-submit').click();
      await page.waitForURL(/\/compare\//, { timeout: 120_000 });

      // F1-L01: el segundo proyecto golpea el límite del plan Gratis
      await page.goto('/projects/new');
      await page.getByTestId('project-name').fill('Segundo proyecto');
      await page.getByTestId('project-submit').click();
      await expect(page.getByText(/Mejora tu plan/)).toBeVisible({ timeout: 15_000 });

      // F2: el panel de consumo muestra 1/1 con aviso y el CTA de upgrade
      await page.goto('/org/usage');
      await expect(page.getByTestId('usage-panel')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByText('1 / 1')).toBeVisible();
      await expect(page.getByText('Límite alcanzado').first()).toBeVisible();
      await expect(page.getByTestId('upgrade-cta')).toBeVisible();
      await expect(page.getByTestId('upgrade-cta')).toContainText('Wompi');
    }
  );
});
