'use client';

import { useDict } from '@/lib/i18n/dictionaries';

export function Faq({ limit }: { limit?: number }) {
  const t = useDict('marketing');

  const items = [
    { q: t.faq1Q, a: t.faq1A },
    { q: t.faq2Q, a: t.faq2A },
    { q: t.faq3Q, a: t.faq3A },
    { q: t.faq4Q, a: t.faq4A },
    { q: t.faq5Q, a: t.faq5A },
    { q: t.faq6Q, a: t.faq6A },
    { q: t.faq7Q, a: t.faq7A },
  ].slice(0, limit ?? 7);

  return (
    <section data-testid="landing-faq" className="max-w-3xl mx-auto px-6 py-16">
      <h2 className="text-2xl font-semibold tracking-tight">{t.faqTitle}</h2>
      <div className="mt-6 flex flex-col gap-2">
        {items.map((item) => (
          <details
            key={item.q}
            className="group rounded-xl border border-border bg-card px-4 py-3"
          >
            <summary className="cursor-pointer list-none text-sm font-medium flex items-center justify-between gap-3">
              {item.q}
              <span className="text-muted-foreground transition-transform group-open:rotate-45">
                +
              </span>
            </summary>
            <p className="mt-2 text-sm text-muted-foreground">{item.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
