import { expect, test } from '../test-with-coverage';

const HELP_MANUAL_BROWSE = ['@flow:help-manual-browse', '@module:home', '@priority:P3'];

test.describe('Manual interactivo', () => {
  test(
    'MAN-F01 — /manual muestra las secciones con sus procesos',
    { tag: [...HELP_MANUAL_BROWSE, '@scenario:man-f01', '@outcome:display'] },
    async ({ page }) => {
      // quality: allow-no-interaction (display-only sheet — the manual renders
      // from a static array with no network call, so there is nothing to drive.
      // The interactive path of this same flow is MAN-F02 below, which types
      // into the search box.)
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
    { tag: [...HELP_MANUAL_BROWSE, '@scenario:man-f02', '@outcome:display'] },
    async ({ page }) => {
      await page.goto('/manual');

      await page.getByPlaceholder('Buscar en el manual…').fill('contraseña');

      await expect(
        page.getByRole('option', { name: /Inicia sesión o recupera tu contraseña/ })
      ).toBeVisible({ timeout: 10_000 });
    }
  );

  test(
    'MAN-F03 — una búsqueda sin coincidencias muestra "Sin resultados"',
    { tag: [...HELP_MANUAL_BROWSE, '@scenario:man-f03', '@outcome:display'] },
    async ({ page }) => {
      // Catches: a Fuse.js threshold/config regression that loosens past 0.4
      // and starts matching everything, or an empty-results branch that
      // silently breaks (renders neither the list nor the "Sin resultados"
      // copy) — see ManualSearch.tsx:140-143 and useManualSearch.ts:46-58.
      await page.goto('/manual');
      await page.getByPlaceholder('Buscar en el manual…').fill('zzznoexistexyz123');

      await expect(page.getByRole('listbox').getByText('Sin resultados')).toBeVisible();
      await expect(page.getByRole('option')).toHaveCount(0);
    }
  );
});
