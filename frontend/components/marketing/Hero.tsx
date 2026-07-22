'use client';

import Link from 'next/link';

import { VersionMock } from '@/components/marketing/VersionMock';
import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';

export function Hero() {
  const t = useDict('marketing');

  return (
    <section className="border-b border-border bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-background via-muted to-background">
      <div className="max-w-6xl mx-auto px-6 py-20 grid grid-cols-1 lg:grid-cols-[1fr_auto] gap-10 items-center">
        <div className="max-w-3xl">
          <p className="inline-flex items-center text-xs font-medium text-foreground bg-card border border-border rounded-full px-3 py-1">
            {t.badge}
          </p>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mt-4">
            {t.heroTitle}
          </h1>
          <p className="mt-4 text-muted-foreground max-w-2xl">{t.heroTagline}</p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link
              data-testid="hero-cta-compare"
              className="bg-primary text-primary-foreground rounded-full px-5 py-3 hover:bg-primary/90 shadow-sm"
              href={ROUTES.COMPARAR}
            >
              {t.heroCtaCompare}
            </Link>
            <Link
              data-testid="hero-cta-signup"
              className="border border-border rounded-full px-5 py-3 hover:bg-accent hover:text-accent-foreground shadow-sm"
              href={ROUTES.SIGN_UP}
            >
              {t.heroCtaSignup}
            </Link>
          </div>
          <p className="mt-3 text-xs text-muted-foreground">{t.heroFinePrint}</p>
        </div>

        <div className="hidden lg:block">
          <VersionMock />
        </div>
      </div>
    </section>
  );
}
