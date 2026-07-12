/**
 * Playwright globalSetup (docs/plan/06 §5.1 — harness gaps H02/H03):
 * 1. Deterministic seed (`create_fake_data --scenario=e2e`).
 * 2. Mint JWTs per role (manage.py e2e_tokens — globalSetup runs before the
 *    webServer, so no HTTP login is possible) and persist them as
 *    storageState cookie files under e2e/.auth/ (gitignored).
 * 3. Purge mailpit so email assertions start clean.
 */

import { execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import path from 'node:path';

const BACKEND = path.resolve(__dirname, '../../backend');
const PYTHON = path.join(BACKEND, 'venv/bin/python');
const AUTH_DIR = path.resolve(__dirname, '.auth');
const MAILPIT_API = process.env.MAILPIT_API ?? 'http://127.0.0.1:8025';

function storageState(tokens: { access: string; refresh: string }) {
  const cookie = (name: string, value: string) => ({
    name,
    value,
    domain: 'localhost',
    path: '/',
    expires: -1,
    httpOnly: false,
    secure: false,
    sameSite: 'Lax' as const,
  });
  return {
    cookies: [cookie('access_token', tokens.access), cookie('refresh_token', tokens.refresh)],
    origins: [],
  };
}

export default async function globalSetup() {
  execFileSync(PYTHON, ['manage.py', 'create_fake_data', '--scenario=e2e'], {
    cwd: BACKEND,
    stdio: 'inherit',
  });

  const raw = execFileSync(PYTHON, ['manage.py', 'e2e_tokens'], { cwd: BACKEND });
  const tokens = JSON.parse(raw.toString()) as Record<string, { access: string; refresh: string }>;

  mkdirSync(AUTH_DIR, { recursive: true });
  for (const [alias, pair] of Object.entries(tokens)) {
    writeFileSync(path.join(AUTH_DIR, `${alias}.json`), JSON.stringify(storageState(pair)));
  }

  try {
    await fetch(`${MAILPIT_API}/api/v1/messages`, { method: 'DELETE' });
  } catch {
    // mailpit down is not fatal for specs that don't assert email
  }
}
