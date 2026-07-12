import AxeBuilder from '@axe-core/playwright';

import { expect, test } from '../test-with-coverage';

/**
 * A11y smoke (DP-18 — docs/plan/04 §6): axe over the key authenticated
 * screens. Gate: ZERO critical violations; serious ones are reported in the
 * assertion message so the fix lands with context.
 */

test.use({ storageState: 'e2e/.auth/editor.json' });

const SCREENS = [
  { path: '/projects', name: 'tablero' },
  { path: '/inbox', name: 'inbox' },
  { path: '/settings', name: 'settings' },
];

for (const screen of SCREENS) {
  test(
    `A11Y-01 — ${screen.name} sin violaciones críticas`,
    { tag: ['@flow:home-loads', '@scenario:a11y-01', '@states'] },
    async ({ page }) => {
      await page.goto(screen.path);
      await page.waitForLoadState('networkidle');

      const results = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa'])
        .analyze();

      const critical = results.violations.filter((v) => v.impact === 'critical');
      const serious = results.violations.filter((v) => v.impact === 'serious');
      expect(
        critical,
        `Violaciones críticas en ${screen.path}: ` +
          critical.map((v) => `${v.id} (${v.nodes.length} nodos)`).join(', ') +
          (serious.length
            ? ` · serias (no bloquean): ${serious.map((v) => v.id).join(', ')}`
            : '')
      ).toEqual([]);
    }
  );
}
