import { renderHook } from '@testing-library/react';
import type { LucideIcon } from 'lucide-react';

import type { ManualProcess, ManualSection } from '../types';
import { useManualSearch } from '../useManualSearch';

const stubIcon = (() => null) as unknown as LucideIcon;

const createProcess = (overrides: Partial<ManualProcess> = {}): ManualProcess => ({
  id: 'seal-approve',
  title: { es: 'Aprueba con tu sello', en: 'Approve with your seal' },
  summary: { es: 'Firma la versión revisada.', en: 'Sign the reviewed version.' },
  why: { es: 'Da validez a la versión.', en: 'It grants the version validity.' },
  steps: {
    es: ['Abre la versión.', 'Presiona sellar.'],
    en: ['Open the version.', 'Press seal.'],
  },
  keywords: ['timbre'],
  ...overrides,
});

const createSection = (overrides: Partial<ManualSection> = {}): ManualSection => ({
  id: 'approvals',
  title: { es: 'Aprobaciones', en: 'Approvals' },
  icon: stubIcon,
  processes: [createProcess()],
  ...overrides,
});

const createManyProcesses = (count: number): ManualProcess[] =>
  Array.from({ length: count }, (_, i) =>
    createProcess({
      id: `guide-${i}`,
      title: { es: `Guía compartida ${i}`, en: `Shared guide ${i}` },
      keywords: [],
    })
  );

describe('useManualSearch', () => {
  it('returns no results for an empty query', () => {
    const { result } = renderHook(() => useManualSearch('', 'es', [createSection()]));

    expect(result.current.results).toEqual([]);
  });

  it('reports an idle search for a whitespace-only query', () => {
    const { result } = renderHook(() => useManualSearch('   ', 'es', [createSection()]));

    expect(result.current.isSearching).toBe(false);
    expect(result.current.activeQuery).toBe('');
  });

  it('finds a process by its title', () => {
    const { result } = renderHook(() =>
      useManualSearch('aprueba', 'es', [createSection()])
    );

    expect(result.current.results[0]?.process.id).toBe('seal-approve');
  });

  it('returns the owning section with each hit', () => {
    const { result } = renderHook(() =>
      useManualSearch('aprueba', 'es', [createSection()])
    );

    expect(result.current.results[0]?.section.id).toBe('approvals');
  });

  it('finds a process by keyword', () => {
    const { result } = renderHook(() =>
      useManualSearch('timbre', 'es', [createSection()])
    );

    expect(result.current.results[0]?.process.id).toBe('seal-approve');
  });

  it('reports an active search with no hits when nothing matches', () => {
    const { result } = renderHook(() =>
      useManualSearch('xyzzy', 'es', [createSection()])
    );

    expect(result.current.results).toEqual([]);
    expect(result.current.isSearching).toBe(true);
  });

  it('caps the results at twelve hits', () => {
    const section = createSection({ processes: createManyProcesses(15) });

    const { result } = renderHook(() => useManualSearch('guía compartida', 'es', [section]));

    expect(result.current.results).toHaveLength(12);
  });

  it('searches the English fields for the en locale', () => {
    const { result } = renderHook(() =>
      useManualSearch('approve', 'en', [createSection()])
    );

    expect(result.current.results[0]?.process.id).toBe('seal-approve');
  });

  it('searches the bundled manual content by default', () => {
    const { result } = renderHook(() => useManualSearch('crear cuenta', 'es'));

    expect(result.current.results.map((hit) => hit.process.id)).toContain('create-account');
  });
});
