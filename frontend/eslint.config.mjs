import { defineConfig, globalIgnores } from 'eslint/config';
import nextVitals from 'eslint-config-next/core-web-vitals';
import nextTs from 'eslint-config-next/typescript';
import playwright from 'eslint-plugin-playwright';
import reactHooks from 'eslint-plugin-react-hooks';

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    ...playwright.configs['flat/recommended'],
    files: ['e2e/**/*.{ts,tsx,js,jsx}'],
    rules: {
      ...playwright.configs['flat/recommended'].rules,
      'playwright/no-conditional-in-test': 'off',
      'playwright/no-conditional-expect': 'off',
      'playwright/expect-expect': 'off',
    },
  },
  {
    files: ['**/__tests__/**/*.{ts,tsx}', 'e2e/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-unused-vars': ['error', {
        varsIgnorePattern: '^_',
        argsIgnorePattern: '^_',
        ignoreRestSiblings: true,
      }],
    },
  },
  {
    files: ['**/__tests__/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    // What still reports here is data fetching and prop->state sync inside
    // effects (`useEffect(() => { void load(); })`) — ordinary React for client
    // components backed by stores. The rule's preferred alternatives belong at
    // the store layer, so this stays VISIBLE as a warning rather than being
    // silenced or forcing an architectural refactor. The project's one genuine
    // suppression lives in lib/hooks/useMounted.ts, with its reason written out.
    // The plugin has to be named here: in flat config a rule is only resolvable
    // in a config object that declares its own plugin.
    plugins: { 'react-hooks': reactHooks },
    rules: {
      'react-hooks/set-state-in-effect': 'warn',
    },
  },
  {
    // Test harness plumbing: Playwright fixtures and the jest setup file wrap
    // third-party objects whose shapes are not worth restating. Same allowance
    // the __tests__ block above already makes, applied to the files that build
    // the harness rather than the ones that use it.
    files: ['e2e/fixtures.ts', 'jest.setup.ts'],
    rules: {
      '@typescript-eslint/no-explicit-any': 'off',
    },
  },
  {
    // `.cjs` is CommonJS by file extension, so `require` is the correct — and
    // only — way to load a dependency there; the rule exists to keep ES modules
    // from reaching for it. The colocated test loads those same modules, which
    // it can only do with require() under jest's CJS runtime.
    files: ['**/*.cjs', 'scripts/__tests__/**/*.{ts,tsx}'],
    rules: {
      '@typescript-eslint/no-require-imports': 'off',
    },
  },
  globalIgnores([
    '.next/**',
    'out/**',
    'build/**',
    'next-env.d.ts',
    'jest.config.cjs',
  ]),
]);

export default eslintConfig;
