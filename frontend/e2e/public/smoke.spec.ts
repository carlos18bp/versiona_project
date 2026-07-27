import { expect, test } from '../test-with-coverage';
import { HOME_LOADS } from '../helpers/flow-tags';

test(
  'public header navigates to the pricing page',
  { tag: [...HOME_LOADS, '@scenario:home-nav-pricing', '@outcome:display'] },
  async ({ page }) => {
    await page.goto('/');

    await page.getByTestId('public-header').getByRole('link', { name: 'Precios' }).click();

    await page.waitForURL(/\/precios/);
    await expect(page.getByRole('heading', { name: 'Planes y precios' })).toBeVisible();
  }
);

test(
  'public footer links the product pages',
  { tag: [...HOME_LOADS, '@scenario:home-footer', '@outcome:display'] },
  async ({ page }) => {
    // quality: allow-no-interaction (footer hrefs are the contract; nav covered by the pricing test)
    await page.goto('/');
    const footer = page.getByTestId('public-footer');

    await expect(footer.getByRole('link', { name: 'Manual' })).toHaveAttribute(
      'href',
      '/manual'
    );
    await expect(footer.getByRole('link', { name: 'Comparar PDFs' })).toHaveAttribute(
      'href',
      '/comparar'
    );
  }
);
