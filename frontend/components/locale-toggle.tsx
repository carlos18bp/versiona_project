'use client';

/**
 * LocaleToggle — one-tap ES ⇄ EN switch over localeStore (persisted).
 * Anonymous visitors get a local preference; authed users still sync their
 * profile language from /settings. Mounted-guard mirrors ThemeToggle.
 */
import { useEffect, useState } from 'react';

import { useLocaleStore } from '@/lib/stores/localeStore';

export function LocaleToggle() {
  const locale = useLocaleStore((s) => s.locale);
  const setLocale = useLocaleStore((s) => s.setLocale);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <div className="h-9 w-9" aria-hidden />;
  }

  const next = locale === 'es' ? 'en' : 'es';

  return (
    <button
      type="button"
      data-testid="locale-toggle"
      aria-label={locale === 'es' ? 'Switch to English' : 'Cambiar a español'}
      onClick={() => setLocale(next)}
      className="inline-flex h-9 items-center justify-center rounded-full px-2.5 text-xs font-semibold uppercase tracking-wide text-foreground hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring transition-colors"
    >
      {next}
    </button>
  );
}
