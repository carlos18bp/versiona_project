'use client';

import Link from 'next/link';

import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';
import { STATIC_PLANS, formatCop } from '@/lib/services/plans';

export function PricingPreview() {
  const t = useDict('marketing');
  const pricing = useDict('pricing');

  return (
    <section data-testid="pricing-preview" className="border-y border-border bg-muted/40">
      <div className="max-w-6xl mx-auto px-6 py-16">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <h2 className="text-2xl font-semibold tracking-tight">{t.pricingPreviewTitle}</h2>
          <Link className="text-sm text-primary hover:underline" href={ROUTES.PRECIOS}>
            {t.pricingPreviewSeeAll} →
          </Link>
        </div>
        <div className="mt-8 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {STATIC_PLANS.map((plan) => (
            <div
              key={plan.key}
              className={`rounded-2xl bg-card border p-5 ${
                plan.key === 'pro' ? 'border-primary/60 ring-1 ring-primary/30' : 'border-border'
              }`}
            >
              <p className="font-medium">{plan.label}</p>
              <p className="mt-1 text-xl font-semibold">
                {plan.price_cop === null
                  ? pricing.contractPricing
                  : plan.price_cop === 0
                    ? pricing.forever
                    : `${formatCop(plan.price_cop)}${pricing.perMonth}`}
              </p>
              {plan.key === 'pro' ? (
                <p className="mt-2 inline-flex rounded-full bg-primary/10 text-primary text-xs px-2 py-0.5">
                  {pricing.trialBadge}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
