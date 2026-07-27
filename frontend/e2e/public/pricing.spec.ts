import { expect, test } from '../test-with-coverage';
import { PUBLIC_PRICING } from '../helpers/flow-tags';

test.describe('Precios públicos', () => {
  test.slow();

  test(
    'PR-F01 — /precios muestra las tres tarjetas con precios COP',
    { tag: [...PUBLIC_PRICING, '@scenario:pr-f01', '@outcome:display'] },
    async ({ page }) => {
      // quality: allow-no-interaction (display contract: concrete COP prices/limits asserted; interactive coverage lives in PR-F03)
      await page.goto('/precios');

      // First hit compiles the route on the dev server — be cold-start tolerant.
      await expect(page.getByTestId('plan-card-free')).toBeVisible({ timeout: 45_000 });
      await expect(page.getByTestId('plan-card-pro')).toBeVisible();
      await expect(page.getByTestId('plan-card-enterprise')).toBeVisible();
      await expect(page.getByTestId('plan-card-pro')).toContainText('Recomendado');
      await expect(page.getByTestId('plan-card-pro')).toContainText('14 días');
      await expect(page.getByTestId('plan-card-pro')).toContainText(/149\.000/);
      await expect(page.getByTestId('plan-card-free')).toContainText(
        'Gratis para siempre'
      );
    }
  );

  test(
    'PR-F02 — la tabla comparativa muestra los límites honestos',
    { tag: [...PUBLIC_PRICING, '@scenario:pr-f02', '@outcome:display'] },
    async ({ page }) => {
      // quality: allow-no-interaction (display contract: concrete COP prices/limits asserted; interactive coverage lives in PR-F03)
      await page.goto('/precios');
      const table = page.getByTestId('pricing-table');

      await expect(table).toBeVisible({ timeout: 20_000 });
      const projectsRow = table.getByRole('row').filter({ hasText: 'Proyectos activos' });
      await expect(projectsRow).toContainText('1');
      await expect(projectsRow).toContainText('20');
      await expect(projectsRow).toContainText('Ilimitado');
      const historyRow = table.getByRole('row').filter({ hasText: 'Historial accesible' });
      await expect(historyRow).toContainText('30 días');
    }
  );

  test(
    'PR-F03 — los CTAs llevan a registro y contacto',
    { tag: [...PUBLIC_PRICING, '@scenario:pr-f03', '@outcome:display'] },
    async ({ page }) => {
      await page.goto('/precios');

      await expect(page.getByTestId('plan-cta-free')).toHaveAttribute('href', '/sign-up');
      await expect(page.getByTestId('plan-cta-enterprise')).toHaveAttribute(
        'href',
        /^mailto:hola@versiona\.app/
      );

      // Click-through real en el CTA de Pro: free ya quedó asserted arriba
      // por href, y enterprise es un mailto: que nunca navega dentro de la app.
      await page.getByTestId('plan-cta-pro').click();
      await page.waitForURL(/\/sign-up/, { timeout: 20_000 });
      await expect(page).toHaveURL(/\/sign-up/);
    }
  );
});
