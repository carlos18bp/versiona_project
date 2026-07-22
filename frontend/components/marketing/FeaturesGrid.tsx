'use client';

import {
  BadgeCheck,
  Crosshair,
  GitCompare,
  History,
  ListChecks,
  ShieldCheck,
} from 'lucide-react';

import { useDict } from '@/lib/i18n/dictionaries';

export function FeaturesGrid() {
  const t = useDict('marketing');

  const features = [
    { Icon: History, title: t.featVersionsTitle, body: t.featVersionsBody, star: false },
    { Icon: GitCompare, title: t.featCompareTitle, body: t.featCompareBody, star: false },
    { Icon: ShieldCheck, title: t.featSealsTitle, body: t.featSealsBody, star: false },
    { Icon: Crosshair, title: t.featInvalidationTitle, body: t.featInvalidationBody, star: true },
    { Icon: BadgeCheck, title: t.featCertsTitle, body: t.featCertsBody, star: false },
    { Icon: ListChecks, title: t.featChecksTitle, body: t.featChecksBody, star: false },
  ];

  return (
    <section data-testid="features-grid" className="border-y border-border bg-muted/40">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <h2 className="text-2xl font-semibold tracking-tight">{t.featuresTitle}</h2>
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map(({ Icon, title, body, star }) => (
            <div
              key={title}
              className={`rounded-2xl bg-card border p-5 ${
                star ? 'border-primary/40 ring-1 ring-primary/20' : 'border-border'
              }`}
            >
              <Icon className={`h-5 w-5 ${star ? 'text-primary' : 'text-muted-foreground'}`} />
              <p className="mt-3 font-medium">{title}</p>
              <p className="mt-1.5 text-sm text-muted-foreground">{body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
