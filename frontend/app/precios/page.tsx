import type { Metadata } from 'next';

import { Faq } from '@/components/marketing/Faq';
import { PricingPlans } from '@/components/marketing/PricingPlans';

export const metadata: Metadata = {
  title: 'Precios — Versiona',
  description:
    'Planes de Versiona: Gratis para siempre, Pro con 14 días de prueba incluidos y Enterprise a la medida. Precios en pesos colombianos (COP).',
};

export default function PreciosPage() {
  return (
    <main>
      <PricingPlans />
      <Faq limit={3} />
    </main>
  );
}
