import { expect, test } from '../../test-with-coverage';
import { A1_ONBOARDING_WOW } from '../../helpers/flow-tags';

/** A1 — fresh guest, NO storageState: sign-up → wizard → a WORKING comparison
 * without uploading anything (metric S1). */

test.describe('A1 — Registro y momento wow', () => {
  test.slow();

  test(
    'A1-F01 — del registro a una comparación funcionando',
    { tag: [...A1_ONBOARDING_WOW, '@scenario:a1-f01', '@scenario:a1-f03'] },
    async ({ page }) => {
      const email = `wow-${Date.now().toString(36)}@versiona.test`;

      // Registro por UI
      await page.goto('/sign-up');
      await page.getByPlaceholder('Email').fill(email);
      await page.getByPlaceholder('Password', { exact: true }).fill('secreta123');
      await page.getByPlaceholder('Confirm password').fill('secreta123');
      await page.getByRole('button', { name: 'Crear cuenta' }).click();

      // El wizard pide el nombre de la organización
      await page.waitForURL(/\/onboarding/, { timeout: 30_000 });
      await expect(page.getByTestId('onboarding-form')).toBeVisible({ timeout: 20_000 });
      await page.getByTestId('onboarding-org-name').fill('Constructora Wow');
      await page.getByTestId('onboarding-submit').click();

      // Aterriza DIRECTO en la comparación del proyecto ejemplo (el wow)
      await page.waitForURL(/\/compare\//, { timeout: 120_000 });
      await expect(page.getByTestId('compare-view')).toBeVisible({ timeout: 30_000 });
      await expect(page.getByText('2 modificadas, 1 eliminada, 1 agregada')).toBeVisible({
        timeout: 30_000,
      });

      // El tablero muestra el proyecto sembrado
      await page.goto('/projects');
      await expect(
        page.getByTestId('projects-grid').getByRole('link', { name: /Proyecto de ejemplo/ })
      ).toBeVisible({ timeout: 15_000 });
    }
  );
});
