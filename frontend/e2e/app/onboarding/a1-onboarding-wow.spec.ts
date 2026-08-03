import { expect, test } from '../../test-with-coverage';
import { A1_ONBOARDING_WOW } from '../../helpers/flow-tags';
import { uniqueEmail } from '../../helpers/versiona';

/** A1 — fresh guest, NO storageState: sign-up → wizard → a WORKING comparison
 * without uploading anything (metric S1). */

test.describe('A1 — Registro y momento wow', () => {
  test.slow();

  test(
    'A1-F01 — del registro a una comparación funcionando',
    { tag: [...A1_ONBOARDING_WOW, '@scenario:a1-f01', '@scenario:a1-f03', '@outcome:success'] },
    async ({ page }) => {
      const email = uniqueEmail('wow');

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

  test(
    'A1-E01 — un 500 de infraestructura durante el seed deja el wizard reintentable',
    { tag: [...A1_ONBOARDING_WOW, '@scenario:a1-e01', '@outcome:failure'] },
    async ({ page }) => {
      // Catches: if `my_onboarding` ever leaks the seed job's raw exception,
      // or the wizard stops resetting `isSeeding` on error, a real storage
      // outage traps the user on an infinite spinner with a disabled button
      // instead of a retryable, visible error.
      const email = uniqueEmail('wow-fail');

      // Registro por UI
      await page.goto('/sign-up');
      await page.getByPlaceholder('Email').fill(email);
      await page.getByPlaceholder('Password', { exact: true }).fill('secreta123');
      await page.getByPlaceholder('Confirm password').fill('secreta123');
      await page.getByRole('button', { name: 'Crear cuenta' }).click();

      await page.waitForURL(/\/onboarding/, { timeout: 30_000 });
      await expect(page.getByTestId('onboarding-form')).toBeVisible({ timeout: 20_000 });

      // Arma el mock DESPUÉS del GET inicial y ANTES del submit: sólo el POST
      // falla (infra outage real: 500 sin cuerpo `{error: ...}`), el GET de
      // estado sigue pasando — así es el fallo real de storage_service.put_bytes.
      await page.route('**/me/onboarding/', (route) => {
        if (route.request().method() === 'POST') {
          return route.fulfill({ status: 500, contentType: 'application/json', body: '{}' });
        }
        return route.continue();
      });

      await page.getByTestId('onboarding-org-name').fill('Constructora Falla');
      await page.getByTestId('onboarding-submit').click();

      // Scoped to the form: Next.js also renders its own route-announcer
      // `role="alert"` element, which would otherwise make this a strict-mode
      // violation (two alerts on the page).
      await expect(
        page.getByTestId('onboarding-form').getByRole('alert')
      ).toHaveText('Algo salió mal', { timeout: 15_000 });
      await expect(page.getByTestId('onboarding-submit')).toBeEnabled();
      expect(page.url()).toContain('/onboarding');
    }
  );
});
