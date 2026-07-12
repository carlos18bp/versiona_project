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
  await page.goto('/projects/new');
  await page.getByTestId('project-name').fill(name);
  await page.getByTestId('project-submit').click();
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
