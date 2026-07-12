import { expect, test } from '../../test-with-coverage';
import { B1_CREATE_PROJECT } from '../../helpers/flow-tags';
import { uniqueName } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('B1 — Crear un proyecto', () => {
  test(
    'B1-F01 — nombre y descripción bastan y aterriza en el proyecto vacío con dropzone-guía',
    { tag: [...B1_CREATE_PROJECT, '@scenario:b1-f01'] },
    async ({ page }) => {
      const name = uniqueName('Licencia');

      await page.goto('/projects/new');
      await page.getByTestId('project-name').fill(name);
      await page.getByTestId('project-description').fill('Expediente ante curaduría');
      await page.getByTestId('project-submit').click();

      await page.waitForURL(/\/projects\/[0-9a-f-]+$/, { timeout: 15_000 });
      await expect(page.getByTestId('upload-dropzone')).toBeVisible();
      await expect(page.getByText('Este proyecto no tiene documentos')).toBeVisible();
    }
  );

  test(
    'B1-E01 — el nombre vacío se rechaza con validación inline',
    { tag: [...B1_CREATE_PROJECT, '@scenario:b1-e01'] },
    async ({ page }) => {
      await page.goto('/projects/new');
      await page.getByTestId('project-submit').click();

      await expect(page.getByText('El nombre es obligatorio')).toBeVisible();
      await expect(page).toHaveURL(/\/projects\/new/);
    }
  );

  test(
    'B1-F01b — el proyecto recién creado aparece en el tablero',
    { tag: [...B1_CREATE_PROJECT, '@scenario:b2-f01'] },
    async ({ page }) => {
      const name = uniqueName('Tablero');
      await page.goto('/projects/new');
      await page.getByTestId('project-name').fill(name);
      await page.getByTestId('project-submit').click();
      await page.waitForURL(/\/projects\/[0-9a-f-]+$/);

      await page.goto('/projects');
      await page.getByTestId('board-search').fill(name);
      await expect(page.getByText(name)).toBeVisible({ timeout: 10_000 });
    }
  );
});
