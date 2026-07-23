import { execFileSync } from 'node:child_process';
import path from 'node:path';

import { expect, test } from '../test-with-coverage';
import { MASTER_JOURNEY } from '../helpers/flow-tags';
import { purgeMailbox, waitForEmail } from '../helpers/mailpit';
import { TESTDATA, uniqueName } from '../helpers/versiona';

/**
 * LA PRUEBA MAESTRA (docs/audit/03 §SS7 — el examen final del producto):
 * dieciséis pasos, tres usuarios reales, todo por la interfaz. Si este spec
 * pasa, Versiona cumple su promesa completa de punta a punta.
 *
 * Única salida de la UI (documentada): el upgrade del plan se hace por consola
 * porque el checkout Wompi está diferido (DECISIÓN PENDIENTE llaves del
 * operador) — es exactamente lo que el operador haría hoy para activar Pro.
 */

const BACKEND = path.resolve(__dirname, '../../../backend');
const BACKEND_API = `http://127.0.0.1:${process.env.E2E_BACKEND_PORT ?? 8000}`;

function upgradeOrgToPro(email: string) {
  execFileSync(
    path.join(BACKEND, 'venv/bin/python'),
    ['manage.py', 'shell', '-c',
     `from orgs.models import Organization;` +
     `org = Organization.objects.get(memberships__user__email='${email}');` +
     `org.plan = 'pro'; org.save(update_fields=['plan'])`],
    { cwd: BACKEND },
  );
}

async function signUp(page: import('@playwright/test').Page, email: string) {
  await page.goto('/sign-up');
  await page.getByPlaceholder('Email').fill(email);
  await page.getByPlaceholder('Password', { exact: true }).fill('secreta123');
  await page.getByPlaceholder('Confirm password').fill('secreta123');
  await page.getByRole('button', { name: 'Crear cuenta' }).click();
  await page.waitForURL(/onboarding/, { timeout: 30_000 });
}

async function uploadVersion(
  page: import('@playwright/test').Page,
  fixture: string,
  { title, message }: { title?: string; message: string }
) {
  await page.getByTestId('upload-input').setInputFiles(path.join(TESTDATA, fixture));
  if (title !== undefined) await page.getByTestId('upload-title').fill(title);
  await page.getByTestId('upload-message').fill(message);
  await page.getByTestId('upload-confirm').click();
  await Promise.race([
    page.getByRole('dialog').waitFor({ state: 'hidden', timeout: 120_000 }),
    page.getByTestId('upload-error').waitFor({ state: 'visible', timeout: 120_000 }),
  ]);
}

test.describe.configure({ mode: 'serial' });

test.describe('M1 — La prueba maestra', () => {
  test(
    'M1 — del registro a la constancia en dieciséis pasos',
    { tag: [...MASTER_JOURNEY, '@scenario:m1', '@states'] },
    async ({ browser }) => {
      test.setTimeout(720_000); // 12 min: tres usuarios y cuatro análisis reales

      const run = Date.now().toString(36);
      const editorEmail = `m1-editor-${run}@versiona.test`;
      const reviewerA = `m1-reva-${run}@versiona.test`;
      const reviewerB = `m1-revb-${run}@versiona.test`;
      await purgeMailbox();

      // ── 1. Registro del editor ────────────────────────────────────────
      const editorContext = await browser.newContext();
      const editor = await editorContext.newPage();
      await signUp(editor, editorEmail);

      // ── 2. Onboarding: nombra la org y ve el wow ─────────────────────
      await editor.getByTestId('onboarding-org-name').fill(`Maestra ${run} SAS`);
      await editor.getByTestId('onboarding-submit').click();
      await editor.waitForURL(/\/compare\//, { timeout: 120_000 });
      await expect(editor.getByTestId('compare-view')).toBeVisible({ timeout: 30_000 });

      // (setup documentado: Pro por consola — Wompi diferido)
      upgradeOrgToPro(editorEmail);

      // ── 3. Crea el proyecto real (B1) ────────────────────────────────
      const projectName = uniqueName('Maestro');
      await editor.goto('/projects/new');
      await editor.getByTestId('project-name').fill(projectName);
      await editor.getByTestId('project-submit').click();
      await editor.waitForURL(/\/projects\/[0-9a-f-]+$/, { timeout: 20_000 });
      const projectUrl = editor.url();

      // ── 4. Sube v1 (C1) ──────────────────────────────────────────────
      const docTitle = `Contrato maestro ${run}`;
      await uploadVersion(editor, 'contrato_v1.pdf', {
        title: docTitle, message: 'v1: primera entrega',
      });
      const documentLink = editor
        .getByTestId('documents-list')
        .getByRole('link', { name: docTitle });
      await expect(documentLink).toBeVisible({ timeout: 120_000 });
      await documentLink.click();
      await expect(editor.getByTestId('version-item-1')).toBeVisible({ timeout: 30_000 });
      const timelineUrl = editor.url();

      // ── 5. Sube v2 (C2: el commit) ───────────────────────────────────
      await uploadVersion(editor, 'contrato_v2.pdf', { message: 'v2: re-entrega' });
      await expect(editor.getByTestId('version-item-2')).toBeVisible({ timeout: 120_000 });

      // ── 6. Compara v1↔v2 (E1: la estrella) ───────────────────────────
      await editor.getByTestId('select-version-1').check();
      await editor.getByTestId('select-version-2').check();
      await editor.getByTestId('compare-selected').click();
      await editor.waitForURL(/\/compare\//, { timeout: 20_000 });
      await expect(
        editor.getByText('2 modificadas, 1 eliminada, 1 agregada')
      ).toBeVisible({ timeout: 30_000 });

      // ── 7. Invita a los revisores A y B (A2) ─────────────────────────
      await editor.goto(projectUrl);
      await editor.getByTestId('project-settings-link').click();
      await expect(editor.getByTestId('members-section')).toBeVisible({ timeout: 20_000 });
      for (const invitee of [reviewerA, reviewerB]) {
        await editor.getByTestId('invite-email').fill(invitee);
        await editor.getByTestId('invite-role').selectOption('reviewer');
        await editor.getByTestId('send-invite').click();
        await expect(
          editor.getByTestId('invitations-list').getByText(invitee)
        ).toBeVisible({ timeout: 15_000 });
      }

      // ── 8. A y B se registran y aceptan (aterrizan en el proyecto) ───
      const contexts: Record<string, import('@playwright/test').Page> = {};
      for (const invitee of [reviewerA, reviewerB]) {
        const email = await waitForEmail({ to: invitee, subjectContains: 'invitó' });
        const detail = await editorContext.request.get(
          `http://127.0.0.1:8025/api/v1/message/${email.ID}`
        );
        const token = ((await detail.json()).Text as string).match(/\/invite\/([\w-]+)/)?.[1];
        expect(token).toMatch(/^[\w-]{20,64}$/);

        const context = await browser.newContext();
        const page = await context.newPage();
        await signUp(page, invitee);
        await page.goto(`/invite/${token}`);
        await page.getByTestId('accept-invitation').click();
        await page.waitForURL(/\/projects\/[0-9a-f-]+$/, { timeout: 20_000 });
        contexts[invitee] = page;
      }
      const pageA = contexts[reviewerA];
      const pageB = contexts[reviewerB];

      // ── 9. B deja una observación anclada a §3 en v2 (D3) ────────────
      await pageB.goto(timelineUrl);
      await expect(pageB.getByTestId('version-item-2')).toBeVisible({ timeout: 30_000 });
      await pageB
        .getByTestId('version-item-2')
        .getByRole('link', { name: 'Ver documento' })
        .click();
      await pageB.waitForURL(/versions\//);
      await expect(pageB.getByTestId('observations-panel')).toBeVisible({ timeout: 30_000 });
      await pageB.getByTestId('add-observation').click();
      await pageB
        .getByTestId('observation-section')
        .selectOption({ label: '3. OBLIGACIONES DEL CONTRATISTA' });
      await pageB
        .getByTestId('observation-body')
        .fill('El plazo de notificación de la multa debe quedar explícito.');
      await pageB.getByTestId('observation-submit').click();
      await expect(pageB.getByText('Abierta')).toBeVisible({ timeout: 20_000 });

      // ── 10. El editor responde y sube v3 que subsana §3 ──────────────
      await editor.goto(timelineUrl);
      await editor
        .getByTestId('version-item-2')
        .getByRole('link', { name: 'Ver documento' })
        .click();
      await editor.waitForURL(/versions\//);
      const replyInput = editor.locator('[data-testid^="reply-input-"]');
      await expect(replyInput).toBeVisible({ timeout: 30_000 });
      await replyInput.fill('Añadimos la notificación escrita con cinco días hábiles.');
      await editor.locator('[data-testid^="reply-send-"]').click();
      await expect(editor.getByText('Respondida')).toBeVisible({ timeout: 20_000 });

      await editor.goto(timelineUrl);
      await uploadVersion(editor, 'contrato_v3.pdf', {
        message: 'v3: subsana la observación de §3',
      });
      await expect(editor.getByTestId('version-item-3')).toBeVisible({ timeout: 120_000 });

      // ── 11. B verifica el re-anclaje en v3 y resuelve (I14) ──────────
      await editor
        .getByTestId('version-item-3')
        .getByRole('link', { name: 'Ver documento' })
        .click();
      await editor.waitForURL(/versions\//);
      const v3Url = editor.url();

      await pageB.goto(v3Url);
      await expect(pageB.getByText(/Re-anclada/)).toBeVisible({ timeout: 30_000 });
      await pageB.locator('[data-testid^="resolve-"]').click();
      await pageB.getByTestId('show-resolved').check();
      await expect(pageB.getByText(/resuelta en v3/)).toBeVisible({ timeout: 20_000 });

      // ── 12. A sella §1–2; B sella el documento completo (D4) ─────────
      await pageA.goto(v3Url);
      await expect(pageA.getByTestId('seal-action-bar')).toBeVisible({ timeout: 30_000 });
      await pageA.getByTestId('seal-sections-open').click();
      await pageA.getByTestId('pick-objeto-del-contrato').check();
      await pageA.getByTestId('pick-definiciones').check();
      await pageA.getByTestId('seal-picked').click();
      await expect(pageA.getByTestId(`seal-${reviewerA}`)).toBeVisible({ timeout: 20_000 });

      await pageB.goto(v3Url);
      await expect(pageB.getByTestId('seal-action-bar')).toBeVisible({ timeout: 30_000 });
      await pageB.getByTestId('seal-all').click();
      await expect(pageB.getByTestId(`seal-${reviewerB}`)).toBeVisible({ timeout: 20_000 });

      // ── 13. v3 queda APROBADA (I10) ──────────────────────────────────
      await editor.reload();
      await expect(
        editor.getByRole('heading', { level: 1 }).locator('..').getByText('Aprobada')
      ).toBeVisible({ timeout: 20_000 });

      // ── 14. v4 dispara la invalidación selectiva (D5 💎) ─────────────
      await editor.goto(timelineUrl);
      await uploadVersion(editor, 'contrato_v4.pdf', {
        message: 'v4: ajusta de nuevo la multa de §3',
      });
      await expect(editor.getByTestId('version-item-4')).toBeVisible({ timeout: 120_000 });
      await editor
        .getByTestId('version-item-4')
        .getByRole('link', { name: 'Ver documento' })
        .click();
      await editor.waitForURL(/versions\//);

      const preservedCard = editor.getByTestId(`validity-${reviewerA}`);
      await expect(preservedCard).toBeVisible({ timeout: 30_000 });
      await expect(preservedCard).toHaveAttribute('data-decision', 'preserved');
      await expect(preservedCard).toContainText('igualdad de hash verificada');
      const invalidatedCard = editor.getByTestId(`validity-${reviewerB}`);
      await expect(invalidatedCard).toHaveAttribute('data-decision', 'invalidated');

      // ── 15. El correo llega SOLO a B; su inbox acota la re-revisión ──
      await waitForEmail({ to: reviewerB, subjectContains: 're-revisión' });
      // A recibió su INVITACIÓN, pero jamás un correo de re-revisión (S6):
      const emailsToA = await editorContext.request.get(
        'http://127.0.0.1:8025/api/v1/search?query=' +
          encodeURIComponent(`to:${reviewerA} subject:"re-revisión"`)
      );
      expect((await emailsToA.json()).messages).toHaveLength(0);
      await pageB.goto('/inbox');
      await expect(
        pageB.getByTestId('inbox-item-seal.invalidated').first()
      ).toBeVisible({ timeout: 20_000 });

      // ── 16. La constancia de v3 se emite y el PDF real se descarga ───
      await editor.goto(v3Url);
      await expect(editor.getByTestId('certificate-panel')).toBeVisible({ timeout: 30_000 });
      const [popup] = await Promise.all([
        editor.waitForEvent('popup', { timeout: 30_000 }),
        editor.getByTestId('issue-certificate').click(),
      ]);
      await popup.close();

      const versionId = v3Url.split('/versions/')[1].split(/[/?#]/)[0];
      const access = (await editorContext.cookies()).find(
        (cookie) => cookie.name === 'access_token'
      )!.value;
      const list = await editor.request.get(
        `${BACKEND_API}/api/versions/${versionId}/certificates/`,
        { headers: { Authorization: `Bearer ${access}` } }
      );
      const certificate = (await list.json()).results[0];
      const download = await editor.request.get(
        `${BACKEND_API}/api/versions/${versionId}/certificates/${certificate.public_id}/download/`,
        { headers: { Authorization: `Bearer ${access}` } }
      );
      const { url, snapshot } = await download.json();
      expect(snapshot.seals).toHaveLength(2); // A y B, ambos vigentes EN v3
      const pdf = await editor.request.get(url);
      expect((await pdf.body()).subarray(0, 4).toString()).toBe('%PDF');

      await editorContext.close();
      for (const page of Object.values(contexts)) await page.context().close();
    }
  );
});
