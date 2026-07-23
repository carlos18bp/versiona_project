import path from 'node:path';

import { expect, test } from '../test-with-coverage';
import { PUBLIC_COMPARE } from '../helpers/flow-tags';
import { TESTDATA } from '../helpers/versiona';

/** It9 — el gancho de adquisición: comparar dos PDF sin cuenta. Los fixtures
 * digitales (truth table v1→v2) evitan OCR y worker: el backend eager procesa
 * en la misma petición. */

test.describe('Comparador público anónimo', () => {
  test.slow();

  test(
    'PC-F01 — un visitante compara dos PDF, ve la truth table y el CTA lo lleva a registro',
    { tag: [...PUBLIC_COMPARE, '@scenario:pc-f01'] },
    async ({ page }) => {
      await page.goto('/comparar');
      await expect(
        page.getByRole('heading', { name: 'Compara dos PDF gratis' })
      ).toBeVisible();

      await page
        .getByTestId('public-file-a')
        .setInputFiles(path.join(TESTDATA, 'contrato_v1.pdf'));
      await page
        .getByTestId('public-file-b')
        .setInputFiles(path.join(TESTDATA, 'contrato_v2.pdf'));
      await page.getByTestId('public-compare-submit').click();

      await page.waitForURL(/\/comparar\/.+/, { timeout: 60_000 });
      await expect(page.getByTestId('public-compare-result')).toBeVisible({
        timeout: 60_000,
      });
      await expect(page.getByTestId('count-modified')).toHaveText('2');
      await expect(page.getByTestId('count-added')).toHaveText('1');
      await expect(page.getByTestId('count-removed')).toHaveText('1');
      await expect(
        page.getByText('2 modificadas, 1 eliminada, 1 agregada')
      ).toBeVisible();

      await expect(page.getByTestId('public-compare-cta')).toBeVisible();
      await page
        .getByTestId('public-compare-cta')
        .getByRole('link', { name: 'Crear cuenta gratis' })
        .click();
      await page.waitForURL(/\/sign-up/);
    }
  );

  test(
    'PC-E01 — un PDF escaneado recibe el mensaje upsell de OCR',
    { tag: [...PUBLIC_COMPARE, '@scenario:pc-e01'] },
    async ({ page }) => {
      await page.goto('/comparar');

      await page
        .getByTestId('public-file-a')
        .setInputFiles(path.join(TESTDATA, 'escaneado_v1.pdf'));
      await page
        .getByTestId('public-file-b')
        .setInputFiles(path.join(TESTDATA, 'contrato_v2.pdf'));
      await page.getByTestId('public-compare-submit').click();

      await expect(page.getByTestId('public-compare-error')).toBeVisible({
        timeout: 30_000,
      });
      await expect(page.getByTestId('public-compare-error')).toContainText('OCR');
      await expect(page.getByTestId('public-compare-error')).toContainText(
        'cuenta gratis'
      );
    }
  );
});
