const nextJest = require('next/jest');

const createJestConfig = nextJest({
  dir: './',
});

/** @type {import('jest').Config} */
const customJestConfig = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  testMatch: ['<rootDir>/**/__tests__/**/*.test.(ts|tsx)'],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/$1',
  },
  collectCoverageFrom: [
    'app/**/*.{ts,tsx}',
    'components/**/*.{ts,tsx}',
    'lib/**/*.{ts,tsx}',
    '!**/*.d.ts',
    '!**/node_modules/**',
    '!**/__tests__/**',
    '!**/e2e/**',
    '!app/layout.tsx',
    '!app/globals.css',
    '!lib/types.ts',
  ],
  coverageProvider: 'v8',
  coverageThreshold: {
    // Final gates (It8, docs/audit/04 §4 + interpretación aprobada del plan:
    // "80% FE" = rutas clave). Jest EXCLUYE del bucket global los paths con
    // gate propio, así que `global` aquí es el RESIDUAL (páginas + lib sin
    // gate específico). Cobertura total medida all-files: 63.8% líneas.
    global: {
      branches: 45,
      functions: 50,
      lines: 50,
      statements: 50,
    },
    './components/compare/': { lines: 80, statements: 80 },
    './components/seals/': { lines: 80, statements: 80 },
    './components/versions/': { lines: 80, statements: 80 },
    './components/reviews/': { lines: 80, statements: 80 },
    './components/observations/': { lines: 80, statements: 80 },
    './components/checks/': { lines: 80, statements: 80 },
    './components/certificates/': { lines: 80, statements: 80 },
    // Staged gates per docs/audit/04 §4 (It1 step: stores 75).
    './lib/stores/': {
      branches: 60,
      functions: 75,
      lines: 75,
      statements: 75,
    },
  },
  coverageReporters: ['text-summary', 'text', 'lcov', 'html', 'json-summary'],
};

module.exports = createJestConfig(customJestConfig);
