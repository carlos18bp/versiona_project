/** Shared UI helpers for the Versiona E2E specs (It1 — flows B1/C1/C2). */

import path from 'node:path';

import { Page, expect } from '@playwright/test';

export const TESTDATA = path.resolve(__dirname, '../../..', 'testdata/pdfs');

export const AUTH = {
  owner: 'e2e/.auth/owner.json',
  admin: 'e2e/.auth/admin.json',
  editor: 'e2e/.auth/editor.json',
  reviewer: 'e2e/.auth/reviewer.json',
  viewer: 'e2e/.auth/viewer.json',
};

export function uniqueName(prefix: string): string {
  return `${prefix} ${Date.now().toString(36)}`;
}

/** B1 happy path — returns the created project name. */
export async function createProject(page: Page, name: string): Promise<void> {
  // Enter through the board and click "Nuevo proyecto" rather than deep-linking
  // to /projects/new. A spec whose first action is a bare goto() to the form
  // never proves the form is reachable — the link could be removed and every
  // caller would still pass. It is also what made four specs carry a baselined
  // `deep_link_entry` finding they never introduced themselves.
  await page.goto('/projects');
  // Generous: this is often the first route a spec touches, and the dev server
  // compiles routes on demand, so a cold /projects can take far longer than the
  // default expect timeout allows.
  const newProjectLink = page.getByRole('link', { name: 'Nuevo proyecto' });
  await expect(newProjectLink).toBeVisible({ timeout: 60_000 });
  await newProjectLink.click();
  await page.waitForURL(/\/projects\/new$/, { timeout: 30_000 });
  await page.getByTestId('project-name').fill(name);
  await page.getByTestId('project-submit').click();
  await expect(page.getByTestId('upload-dropzone')).toBeVisible({ timeout: 15_000 });
}

/** Opens the seeded multi-role project (Torre E2E): the ONLY project where all
 * five seeded actors are members — required by multi-user specs (d4/d5) until
 * the invitations UI arrives (A2, It6). */
export async function openSeededProject(page: Page): Promise<void> {
  await page.goto('/projects');
  await page.getByTestId('board-search').fill('Torre E2E');
  const card = page.getByTestId('projects-grid').getByRole('link', { name: /Torre E2E/ });
  await card.first().click();
  await expect(page.getByTestId('upload-dropzone')).toBeVisible({ timeout: 15_000 });
}

/** C1/C2 happy path: pick a fixture, confirm the preview, wait for analysis. */
export async function uploadPdf(
  page: Page,
  fixture: string,
  { message = '', title }: { message?: string; title?: string } = {}
): Promise<void> {
  await page.getByTestId('upload-input').setInputFiles(path.join(TESTDATA, fixture));
  if (title !== undefined) {
    await page.getByTestId('upload-title').fill(title);
  }
  if (message) {
    await page.getByTestId('upload-message').fill(message);
  }
  await page.getByTestId('upload-confirm').click();
  // The preview closes when the analysis job finishes; a rejected upload keeps
  // it open with an error. Wait for whichever happens (no fixed timeouts).
  await Promise.race([
    page.getByRole('dialog').waitFor({ state: 'hidden', timeout: 90_000 }),
    page.getByTestId('upload-error').waitFor({ state: 'visible', timeout: 90_000 }),
  ]);
}
