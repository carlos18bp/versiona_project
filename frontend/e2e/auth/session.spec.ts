import { expect, test } from '../test-with-coverage';
import { AUTH_SIGN_IN_SUCCESS, AUTH_SIGN_OUT } from '../helpers/flow-tags';

test.describe('Real session', () => {
  test(
    'U8 — sign-in with seeded credentials creates a session and lands on the board',
    { tag: [...AUTH_SIGN_IN_SUCCESS, '@scenario:u8'] },
    async ({ page }) => {
      await page.goto('/sign-in');
      await page.getByPlaceholder('Email').fill('editor@versiona.test');
      await page.getByPlaceholder('Password').fill('secreta123');
      await page.getByRole('button', { name: /sign in/i }).click();

      await page.waitForURL(/\/(projects|dashboard)/, { timeout: 20_000 });
      await expect(page.getByRole('button', { name: 'Salir' })).toBeVisible();

      const cookies = await page.context().cookies();
      expect(cookies.some((cookie) => cookie.name === 'access_token' && cookie.value)).toBe(true);
    }
  );

  test(
    'U9 — sign-out clears the session and protected routes redirect again',
    { tag: [...AUTH_SIGN_OUT, '@scenario:u9'] },
    async ({ browser }) => {
      const context = await browser.newContext({ storageState: 'e2e/.auth/viewer.json' });
      const page = await context.newPage();
      await page.goto('/projects');
      await expect(page.getByRole('button', { name: 'Salir' })).toBeVisible();

      await page.getByRole('button', { name: 'Salir' }).click();
      // useRequireAuth redirects the protected page to /sign-in on sign-out
      await page.waitForURL(/sign-in/, { timeout: 15_000 });

      const cookies = await page.context().cookies();
      expect(cookies.some((cookie) => cookie.name === 'access_token' && cookie.value)).toBe(false);

      await page.goto('/projects');
      await page.waitForURL(/sign-in/);
      await context.close();
    }
  );
});
