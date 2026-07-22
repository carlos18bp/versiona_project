import { expect, test } from '../test-with-coverage';
import { HOME_LOADS } from '../helpers/flow-tags';

test('home page loads', { tag: [...HOME_LOADS] }, async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'El Git de tus documentos' })).toBeVisible();
});

test(
  'landing shows the dual CTA (comparator + trial signup)',
  { tag: [...HOME_LOADS, '@scenario:home-cta'] },
  async ({ page }) => {
    await page.goto('/');

    await expect(page.getByTestId('hero-cta-compare')).toHaveAttribute('href', '/comparar');
    await expect(page.getByTestId('hero-cta-signup')).toHaveAttribute('href', '/sign-up');
    await expect(page.getByTestId('hero-cta-signup')).toContainText('14 días');
  }
);

test(
  'landing renders the honest marketing sections',
  { tag: [...HOME_LOADS, '@scenario:home-sections'] },
  async ({ page }) => {
    await page.goto('/');

    await expect(page.getByTestId('how-it-works')).toBeVisible();
    await expect(page.getByTestId('features-grid')).toBeVisible();
    await expect(page.getByTestId('tech-strip')).toBeVisible();
    await expect(page.getByTestId('pricing-preview')).toBeVisible();
    await expect(page.getByTestId('landing-faq')).toBeVisible();
  }
);

test(
  'public header navigates to the pricing page',
  { tag: [...HOME_LOADS, '@scenario:home-nav-pricing'] },
  async ({ page }) => {
    await page.goto('/');

    await page.getByTestId('public-header').getByRole('link', { name: 'Precios' }).click();

    await page.waitForURL(/\/precios/);
    await expect(page.getByRole('heading', { name: 'Planes y precios' })).toBeVisible();
  }
);

test(
  'public footer links the product pages',
  { tag: [...HOME_LOADS, '@scenario:home-footer'] },
  async ({ page }) => {
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
