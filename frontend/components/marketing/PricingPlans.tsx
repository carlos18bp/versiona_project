'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';

import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { Skeleton } from '@/components/ui/Skeleton';
import { ROUTES } from '@/lib/constants';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import {
  fetchPublicPlans,
  formatCop,
  type PublicPlan,
  type PublicPlansResult,
} from '@/lib/services/plans';

const ENTERPRISE_MAILTO = 'mailto:hola@versiona.app?subject=Plan%20Enterprise';

export function PricingPlans() {
  const pricing = useDict('pricing');
  const [result, setResult] = useState<PublicPlansResult | null>(null);

  function priceLine(plan: PublicPlan) {
    if (plan.price_cop === null) return pricing.contractPricing;
    if (plan.price_cop === 0) return pricing.forever;
    return `${formatCop(plan.price_cop)}${pricing.perMonth}`;
  }

  function limitCell(value: number | null, asDays = false) {
    if (value === null) return pricing.unlimited;
    if (asDays) return interpolate(pricing.days, { days: value });
    return String(value);
  }

  useEffect(() => {
    let cancelled = false;
    void fetchPublicPlans().then((data) => {
      if (!cancelled) setResult(data);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const plans = result?.plans ?? [];
  const descriptions: Record<PublicPlan['key'], string> = {
    free: pricing.freeDesc,
    pro: pricing.proDesc,
    enterprise: pricing.enterpriseDesc,
  };

  return (
    <section className="max-w-6xl mx-auto px-6 py-16">
      <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">{pricing.title}</h1>
      <p className="mt-3 text-muted-foreground">{pricing.subtitle}</p>

      <AsyncBoundary
        isLoading={result === null}
        error={null}
        skeleton={
          <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Skeleton className="h-56 w-full rounded-2xl" />
            <Skeleton className="h-56 w-full rounded-2xl" />
            <Skeleton className="h-56 w-full rounded-2xl" />
          </div>
        }
      >
        {result?.fromFallback ? (
          <div data-testid="pricing-fallback" className="hidden" aria-hidden />
        ) : null}

        <div className="mt-10 grid grid-cols-1 sm:grid-cols-3 gap-4">
          {plans.map((plan) => (
            <div
              key={plan.key}
              data-testid={`plan-card-${plan.key}`}
              className={`rounded-2xl bg-card border p-6 flex flex-col ${
                plan.key === 'pro'
                  ? 'border-primary/60 ring-2 ring-primary/30'
                  : 'border-border'
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <p className="text-lg font-semibold">{plan.label}</p>
                {plan.key === 'pro' ? (
                  <span className="rounded-full bg-primary text-primary-foreground text-xs px-2.5 py-1">
                    {pricing.recommended}
                  </span>
                ) : null}
              </div>
              <p className="mt-2 text-2xl font-bold">{priceLine(plan)}</p>
              {plan.key === 'pro' ? (
                <p className="mt-2 inline-flex self-start rounded-full bg-primary/10 text-primary text-xs px-2.5 py-1">
                  {pricing.trialBadge}
                </p>
              ) : null}
              <p className="mt-3 text-sm text-muted-foreground">{descriptions[plan.key]}</p>

              <div className="mt-6 flex flex-col gap-2">
                {plan.key === 'free' ? (
                  <Link
                    data-testid="plan-cta-free"
                    className="rounded-full border border-border px-4 py-2.5 text-center text-sm hover:bg-accent hover:text-accent-foreground"
                    href={ROUTES.SIGN_UP}
                  >
                    {pricing.ctaFree}
                  </Link>
                ) : null}
                {plan.key === 'pro' ? (
                  <>
                    <Link
                      data-testid="plan-cta-pro"
                      className="rounded-full bg-primary text-primary-foreground px-4 py-2.5 text-center text-sm hover:bg-primary/90"
                      href={ROUTES.SIGN_UP}
                    >
                      {pricing.ctaPro}
                    </Link>
                    <p className="text-xs text-muted-foreground">{pricing.proNote}</p>
                  </>
                ) : null}
                {plan.key === 'enterprise' ? (
                  <a
                    data-testid="plan-cta-enterprise"
                    className="rounded-full border border-border px-4 py-2.5 text-center text-sm hover:bg-accent hover:text-accent-foreground"
                    href={ENTERPRISE_MAILTO}
                  >
                    {pricing.ctaEnterprise}
                  </a>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-12 overflow-x-auto">
          <table data-testid="pricing-table" className="w-full min-w-[540px] text-sm">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="py-3 pr-4 font-medium">{pricing.tableFeature}</th>
                {plans.map((plan) => (
                  <th key={plan.key} className="py-3 px-4 font-medium">
                    {plan.label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="text-muted-foreground">
              <tr className="border-b border-border">
                <td className="py-3 pr-4">{pricing.rowProjects}</td>
                {plans.map((plan) => (
                  <td key={plan.key} className="py-3 px-4">
                    {limitCell(plan.limits.max_active_projects)}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-border">
                <td className="py-3 pr-4">{pricing.rowMembers}</td>
                {plans.map((plan) => (
                  <td key={plan.key} className="py-3 px-4">
                    {limitCell(plan.limits.max_members)}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-border">
                <td className="py-3 pr-4">{pricing.rowHistory}</td>
                {plans.map((plan) => (
                  <td key={plan.key} className="py-3 px-4">
                    {limitCell(plan.limits.history_days, true)}
                  </td>
                ))}
              </tr>
              <tr>
                <td className="py-3 pr-4">{pricing.rowCore}</td>
                {plans.map((plan) => (
                  <td key={plan.key} className="py-3 px-4">
                    <Check
                      className="h-4 w-4 text-success"
                      aria-label={pricing.included}
                    />
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </AsyncBoundary>
    </section>
  );
}
