import { expect, test } from '../../test-with-coverage';
import { B2_PROJECTS_BOARD } from '../../helpers/flow-tags';
import { createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('B2 — Tablero completo', () => {
  test.slow();

  test(
    'B2-A03 — la búsqueda encuentra el proyecto por CONTENIDO del PDF',
    { tag: [...B2_PROJECTS_BOARD, '@scenario:b2-a03', '@scenario:b2-a01'] },
    async ({ page }) => {
      // Proyecto fresco cuyo NOMBRE no contiene el término: si aparece al
      // buscar, la coincidencia vino del contenido del PDF.
      const name = uniqueName('Zulia');
      await createProject(page, name);
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'Contenido', message: 'v1' });
      await expect(
        page.getByTestId('documents-list').getByRole('link', { name: 'Contenido' })
      ).toBeVisible({ timeout: 90_000 });

      // 'interventoría' vive DENTRO del PDF (sin acento en el binario: la
      // búsqueda es insensible a acentos vía unaccent)
      await page.goto('/projects');
      await page.getByTestId('board-search').fill('interventoría');
      await expect(
        page.getByTestId('projects-grid').getByRole('link', { name })
      ).toBeVisible({ timeout: 15_000 });

      // Una búsqueda sin coincidencias muestra el vacío-con-guía
      await page.getByTestId('board-search').fill('blockchain quantum');
      await expect(page.getByTestId('projects-grid')).toHaveCount(0, { timeout: 15_000 });

      // El filtro de estado lista el proyecto activo
      await page.getByTestId('board-search').fill('');
      await page.getByTestId('board-status-filter').selectOption('active');
      await expect(
        page.getByTestId('projects-grid').getByRole('link', { name })
      ).toBeVisible({ timeout: 15_000 });
    }
  );
});
