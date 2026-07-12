import path from 'node:path';

import { expect, test } from '../../test-with-coverage';
import { C1_UPLOAD_FIRST } from '../../helpers/flow-tags';
import { TESTDATA, createProject, uniqueName, uploadPdf } from '../../helpers/versiona';

test.use({ storageState: 'e2e/.auth/editor.json' });

test.describe('C1 — Subir el primer documento', () => {
  test(
    'C1-F01 — drag&drop con preview local, análisis y v1 con secciones indexadas',
    { tag: [...C1_UPLOAD_FIRST, '@scenario:c1-f01', '@scenario:c1-a01'] },
    async ({ page }) => {
      await createProject(page, uniqueName('Contratos'));

      await uploadPdf(page, 'contrato_v1.pdf', {
        title: 'Contrato de obra',
        message: 'primera entrega',
      });

      // El job termina, el preview se cierra y la lista muestra el documento
      await expect(page.getByTestId('documents-list')).toBeVisible({ timeout: 90_000 });
      const documentLink = page
        .getByTestId('documents-list')
        .getByRole('link', { name: /Contrato de obra/ });
      await expect(documentLink).toBeVisible();

      // Abrir el timeline: v1 lista con su semáforo de análisis
      await documentLink.click();
      await expect(page.getByTestId('version-item-1')).toBeVisible({ timeout: 15_000 });
      await expect(page.getByText('Versión lista')).toBeVisible();

      // Abrir el visor: las secciones del contrato están indexadas
      await page.getByRole('link', { name: 'Ver documento' }).click();
      await expect(page.getByTestId('sections-list')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByText('1. OBJETO DEL CONTRATO')).toBeVisible();
      await expect(page.getByText('8. RESOLUCION DE CONTROVERSIAS')).toBeVisible();
    }
  );

  test(
    'C1-E01 — un PDF protegido se rechaza con mensaje accionable antes de subir',
    { tag: [...C1_UPLOAD_FIRST, '@scenario:c1-e01'] },
    async ({ page }) => {
      await createProject(page, uniqueName('Protegidos'));

      await page
        .getByTestId('upload-input')
        .setInputFiles(path.join(TESTDATA, 'protegido.pdf'));

      // El preview local lo rechaza sin gastar red (kit 1); el backend lo
      // rechaza igual (cubierto en integración: test_version_service).
      await expect(page.getByTestId('pdf-error')).toContainText('contraseña', {
        timeout: 30_000,
      });
      await page.getByRole('button', { name: 'Cancelar' }).click();
      await expect(page.getByTestId('upload-dropzone')).toBeVisible();
    }
  );
});
