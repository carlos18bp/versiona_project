'use client';

import { useDict } from '@/lib/i18n/dictionaries';

export function HowItWorks() {
  const t = useDict('marketing');

  const steps = [
    { title: t.how1Title, body: t.how1Body },
    { title: t.how2Title, body: t.how2Body },
    { title: t.how3Title, body: t.how3Body },
  ];

  return (
    <section data-testid="how-it-works" className="max-w-6xl mx-auto px-6 py-16">
      <h2 className="text-2xl font-semibold tracking-tight">{t.howTitle}</h2>
      <ol className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {steps.map((step, index) => (
          <li key={step.title} className="rounded-2xl bg-card border border-border p-5">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-primary/10 text-primary text-sm font-semibold">
              {index + 1}
            </span>
            <p className="mt-3 font-medium">{step.title}</p>
            <p className="mt-1.5 text-sm text-muted-foreground">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}
