import { expect, test } from '../test-with-coverage';

const HELP_MANUAL_BROWSE = ['@flow:help-manual-browse', '@module:home', '@priority:P3'];

test.describe('Manual interactivo', () => {
  test(
    'MAN-F01 — /manual muestra las secciones con sus procesos',
    { tag: [...HELP_MANUAL_BROWSE, '@scenario:man-f01'] },
    async ({ page }) => {
      await page.goto('/manual');

      await expect(
        page.getByRole('heading', { level: 1, name: /manual/i })
      ).toBeVisible({ timeout: 20_000 });
      await expect(
        page.getByRole('heading', { name: 'Primeros pasos' }).first()
      ).toBeVisible();
      await expect(
        page.getByRole('heading', { name: 'Crea tu cuenta' })
      ).toBeVisible();
    }
  );

  test(
    'MAN-F02 — la búsqueda filtra procesos por texto',
    { tag: [...HELP_MANUAL_BROWSE, '@scenario:man-f02'] },
    async ({ page }) => {
      await page.goto('/manual');

      await page.getByPlaceholder('Buscar en el manual…').fill('contraseña');

      await expect(
        page.getByRole('option', { name: /Inicia sesión o recupera tu contraseña/ })
      ).toBeVisible({ timeout: 10_000 });
    }
  );
});
