import { test, expect } from '../test-with-coverage';
import { waitForPageLoad } from '../fixtures';
import { AUTH_SIGN_IN_FORM, AUTH_SIGN_UP_FORM, AUTH_LOGIN_INVALID, AUTH_PROTECTED_REDIRECT, AUTH_FORGOT_PASSWORD_FORM } from '../helpers/flow-tags';

test.describe('Authentication', () => {
  test('should show validation on empty form submission', { tag: [...AUTH_SIGN_IN_FORM] }, async ({ page }) => {
    await page.goto('/sign-in');
    await waitForPageLoad(page);
    
    // Try to submit empty form
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();
    
    // Should still be on sign-in page
    await expect(page).toHaveURL(/.*sign-in/);
  });

  test('should accept input in form fields', { tag: [...AUTH_SIGN_IN_FORM] }, async ({ page }) => {
    await page.goto('/sign-in');
    await waitForPageLoad(page);
    
    // Fill email (using placeholder)
    const emailInput = page.getByPlaceholder('Email');
    await emailInput.fill('test@example.com');
    await expect(emailInput).toHaveValue('test@example.com');
    
    // Fill password
    const passwordInput = page.locator('input[type="password"]');
    await passwordInput.fill('password123');
    await expect(passwordInput).toHaveValue('password123');
  });

  test('should handle invalid credentials gracefully', { tag: [...AUTH_LOGIN_INVALID] }, async ({ page }) => {
    await page.goto('/sign-in');
    await waitForPageLoad(page);
    
    // Fill with invalid credentials (using placeholder)
    const emailInput = page.getByPlaceholder('Email');
    await emailInput.fill('invalid@example.com');
    
    const passwordInput = page.locator('input[type="password"]');
    await passwordInput.fill('wrongpassword');
    
    // Submit
    const submitBtn = page.locator('button[type="submit"]');
    await submitBtn.click();
    
    // Should show error or stay on sign-in page
    await expect(page).toHaveURL(/.*sign-in/);
  });

  test('should redirect anonymous users away from the dashboard', { tag: [...AUTH_PROTECTED_REDIRECT] }, async ({ page }) => {
    // quality: allow-no-interaction (authorization gate fires on navigation itself — redirect guard; no user action exists to drive)
    await page.goto('/dashboard');
    await waitForPageLoad(page);

    // Anonymous context (no storageState): /dashboard hard-redirects to
    // /projects (app/dashboard/page.tsx), and the useRequireAuth guard that
    // gates /projects then bounces the unauthenticated visitor to /sign-in
    // before projects-grid ever mounts.
    await expect(page).toHaveURL(/\/sign-in/);
    await expect(page.getByTestId('projects-grid')).toHaveCount(0);
  });

  test('should validate password mismatch on sign-up', { tag: [...AUTH_SIGN_UP_FORM] }, async ({ page }) => {
    await page.goto('/sign-up');
    await waitForPageLoad(page);

    // Fill form with mismatched passwords
    await page.getByPlaceholder('First Name').fill('Test');
    await page.getByPlaceholder('Last Name').fill('User');
    await page.getByPlaceholder('Email').fill('test@example.com');
    await page.getByPlaceholder('Password', { exact: true }).fill('password123');
    await page.getByPlaceholder('Confirm Password').fill('different456');

    await page.getByRole('button', { name: 'Crear cuenta' }).click();

    // Should show password mismatch error and stay on sign-up page
    await expect(page.getByText('Las contraseñas no coinciden')).toBeVisible();
    await expect(page).toHaveURL(/.*sign-up/);
  });

  test('should navigate from sign-in to forgot password', { tag: [...AUTH_FORGOT_PASSWORD_FORM] }, async ({ page }) => {
    await page.goto('/sign-in');
    await waitForPageLoad(page);

    // Click forgot password link
    const forgotLink = page.getByRole('link', { name: '¿Olvidaste tu contraseña?' });
    await expect(forgotLink).toBeVisible();
    await forgotLink.click();
    await page.waitForURL(/.*forgot-password/, { timeout: 10_000 });

    await expect(page).toHaveURL(/.*forgot-password/);
    await expect(page.getByRole('heading', { name: 'Reset Password' })).toBeVisible();
  });
});
