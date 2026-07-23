import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '../test-with-coverage';

const ADMIN_LOGIN_HANDOFF = ['@flow:auth-admin-login-handoff', '@module:auth', '@priority:P3'];
const BACKEND = path.resolve(__dirname, '../../../backend');

function mintTokens(): { access: string; refresh: string } {
  const raw = execFileSync(
    path.join(BACKEND, 'venv/bin/python'),
    ['manage.py', 'e2e_tokens'],
    { cwd: BACKEND, encoding: 'utf-8' }
  );
  return JSON.parse(raw).owner;
}

test.describe('Handoff desde el admin de Django', () => {
  test(
    'ADM-E01 — sin tokens el handoff rebota a sign-in',
    { tag: [...ADMIN_LOGIN_HANDOFF, '@scenario:adm-e01'] },
    async ({ page }) => {
      await page.goto('/admin-login');

      await page.waitForURL(/\/sign-in/, { timeout: 20_000 });
      await expect(page.getByPlaceholder('Email')).toBeVisible();
    }
  );

  test(
    'ADM-F01 — con tokens reales aterriza autenticado en el destino',
    { tag: [...ADMIN_LOGIN_HANDOFF, '@scenario:adm-f01'] },
    async ({ page }) => {
      const { access, refresh } = mintTokens();

      await page.goto(
        `/admin-login?access=${access}&refresh=${refresh}&redirect=/projects`
      );

      await page.waitForURL(/\/projects/, { timeout: 30_000 });
      await expect(page.getByRole('button', { name: 'Salir' })).toBeVisible({
        timeout: 20_000,
      });
    }
  );
});
