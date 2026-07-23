import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '../../test-with-coverage';
import { F1_BILLING, F2_USAGE_PANEL } from '../../helpers/flow-tags';

/** F1+F2 sobre una cuenta FRESCA: todo registro nuevo estrena el trial Pro de
 * 14 días (It9), así que primero se verifica el estado de prueba y luego se
 * EXPIRA por consola (lo que haría el paso del tiempo) para ejercitar los
 * límites del plan Gratis: el ejemplo del onboarding llena el cupo de 1
 * proyecto y el segundo golpea el límite con el diálogo de upgrade. */

const BACKEND = path.resolve(__dirname, '../../../../backend');

function expireTrial(email: string) {
  execFileSync(
    path.join(BACKEND, 'venv/bin/python'),
    ['manage.py', 'shell', '-c',
     `from datetime import timedelta;` +
     `from django.utils import timezone;` +
     `from billing.models import Subscription;` +
     `sub = Subscription.objects.get(organization__memberships__user__email='${email}');` +
     `sub.trial_ends_at = timezone.now() - timedelta(days=1);` +
     `sub.status = 'expired'; sub.save()`],
    { cwd: BACKEND },
  );
}

test.describe('F1+F2 — Límites del plan y consumo', () => {
  test.slow();

  test(
    'F1-L01/F2-F01 — el trial arranca, al expirar el límite bloquea con diálogo y el panel avisa',
    { tag: [...F1_BILLING, ...F2_USAGE_PANEL, '@scenario:f1-l01', '@scenario:f2-f01'] },
    async ({ page }) => {
      const email = `free-${Date.now().toString(36)}@versiona.test`;

      // Registro + onboarding (siembra el proyecto ejemplo ⇒ 1 activo)
      await page.goto('/sign-up');
      await page.getByPlaceholder('Email').fill(email);
      await page.getByPlaceholder('Password', { exact: true }).fill('secreta123');
      await page.getByPlaceholder('Confirm password').fill('secreta123');
      await page.getByRole('button', { name: 'Crear cuenta' }).click();
      await page.waitForURL(/onboarding/, { timeout: 30_000 });
      await page.getByTestId('onboarding-org-name').fill('Limitada SAS');
      await page.getByTestId('onboarding-submit').click();
      await page.waitForURL(/\/compare\//, { timeout: 120_000 });

      // It9: la cuenta fresca está en prueba Pro — el panel lo dice
      await page.goto('/org/usage');
      await expect(page.getByTestId('usage-panel')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByTestId('usage-trial-line')).toBeVisible();

      // La prueba termina (consola = paso del tiempo) ⇒ plan Gratis efectivo
      expireTrial(email);

      // F1-L01: el segundo proyecto golpea el límite ⇒ diálogo de upgrade
      await page.goto('/projects/new');
      await page.getByTestId('project-name').fill('Segundo proyecto');
      await page.getByTestId('project-submit').click();
      await expect(page.getByTestId('upgrade-dialog')).toBeVisible({ timeout: 15_000 });
      await expect(page.getByTestId('upgrade-dialog')).toContainText('Mejora tu plan');
      await expect(page.getByTestId('upgrade-dialog-plans')).toHaveAttribute(
        'href',
        '/precios'
      );
      await page.getByRole('button', { name: 'Cerrar diálogo' }).click();

      // F2: el panel muestra 1/1 con aviso y el CTA lleva a /precios
      await page.goto('/org/usage');
      await expect(page.getByTestId('usage-panel')).toBeVisible({ timeout: 20_000 });
      await expect(page.getByText('1 / 1')).toBeVisible();
      await expect(page.getByText('Límite alcanzado').first()).toBeVisible();
      await expect(page.getByTestId('upgrade-cta')).toBeVisible();
      await expect(page.getByTestId('upgrade-plans-link')).toHaveAttribute(
        'href',
        '/precios'
      );
      await expect(page.getByTestId('upgrade-contact')).toBeVisible();

      // De-orfanado: el panel es alcanzable desde el header autenticado
      await page.goto('/projects');
      await page.getByTestId('nav-plan-usage').click();
      await page.waitForURL(/org\/usage/);
      await expect(page.getByTestId('usage-panel')).toBeVisible({ timeout: 20_000 });

      // …y también desde /settings
      await page.goto('/settings');
      await page.getByTestId('settings-usage-link').click();
      await page.waitForURL(/org\/usage/);
      await expect(page.getByTestId('usage-panel')).toBeVisible({ timeout: 20_000 });
    }
  );
});
