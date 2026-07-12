import { expect, test } from '../../test-with-coverage';
import { E1_COMPARE } from '../../helpers/flow-tags';
import { createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('E1 — Comparar dos versiones (pantalla estrella)', () => {
  test.slow(); // two real upload+analysis cycles before the comparison

  test(
    'E1-F01/F02 — las tres vistas muestran la tabla de verdad exacta',
    { tag: [...E1_COMPARE, '@scenario:e1-f01', '@scenario:e1-f02', '@scenario:c3-a01'] },
    async ({ page }) => {
      await createProject(page, uniqueName('Comparación'));
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'Contrato C', message: 'v1' });
      const documentLink = page
        .getByTestId('documents-list')
        .getByRole('link', { name: /Contrato C/ });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });

      await uploadPdf(page, 'contrato_v2.pdf', { message: 'v2' });
      await expect(page.getByTestId('version-item-2')).toBeVisible({ timeout: 90_000 });

      // C3-A01: elegir dos versiones desde el timeline y comparar
      await expect(page.getByTestId('compare-selected')).toBeDisabled();
      await page.getByTestId('select-version-1').check();
      await page.getByTestId('select-version-2').check();
      await page.getByTestId('compare-selected').click();
      await page.waitForURL(/\/compare\//, { timeout: 20_000 });

      // Vista lado a lado (default): ambos visores + lista de secciones
      await expect(page.getByTestId('compare-view')).toBeVisible({ timeout: 30_000 });
      await expect(page.getByTestId('side-before')).toBeVisible();
      await expect(page.getByTestId('side-after')).toBeVisible();
      await expect(page.getByText('2 modificadas, 1 eliminada, 1 agregada')).toBeVisible();

      // Vista de secciones: la tabla de verdad EXACTA
      await page.getByRole('tab', { name: 'Secciones' }).click();
      const list = page.getByTestId('section-change-list');
      await expect(list).toBeVisible();
      await expect(page.getByTestId('section-obligaciones-del-contratista')).toHaveAttribute(
        'data-change',
        'modified'
      );
      await expect(page.getByTestId('section-valor-y-forma-de-pago')).toHaveAttribute(
        'data-change',
        'modified'
      );
      await expect(page.getByTestId('section-plazo-de-ejecucion')).toHaveAttribute(
        'data-change',
        'removed'
      );
      await expect(page.getByTestId('section-proteccion-de-datos-personales')).toHaveAttribute(
        'data-change',
        'added'
      );
      // Las secciones renumeradas (7→6, 8→7) NO son cambios
      await expect(page.getByTestId('section-confidencialidad')).toHaveCount(0);

      // Vista de resumen: los conteos exactos
      await page.getByRole('tab', { name: 'Resumen' }).click();
      await expect(page.getByTestId('count-modified')).toHaveText('2');
      await expect(page.getByTestId('count-removed')).toHaveText('1');
      await expect(page.getByTestId('count-added')).toHaveText('1');

      // E1-F02: seleccionar una sección deja el deep-link en la URL
      await page.getByRole('tab', { name: 'Secciones' }).click();
      await page.getByTestId('section-obligaciones-del-contratista').click();
      await expect(page).toHaveURL(/#sec-obligaciones-del-contratista/);
    }
  );

  test(
    'E1-L01 — comparar una versión consigo misma no ofrece pares inválidos',
    { tag: [...E1_COMPARE, '@scenario:e1-l01'] },
    async ({ page }) => {
      await createProject(page, uniqueName('SinCambios'));
      await uploadPdf(page, 'contrato_v1.pdf', { title: 'Único', message: 'v1' });
      const documentLink = page
        .getByTestId('documents-list')
        .getByRole('link', { name: /Único/ });
      await expect(documentLink).toBeVisible({ timeout: 90_000 });
      await documentLink.click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 20_000 });

      // Con una sola versión, comparar queda deshabilitado (C2-L01)
      await page.getByTestId('select-version-1').check();
      await expect(page.getByTestId('compare-selected')).toBeDisabled();
    }
  );
});
