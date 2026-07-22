import type { Metadata } from 'next';

import { Faq } from '@/components/marketing/Faq';
import { FeaturesGrid } from '@/components/marketing/FeaturesGrid';
import { Hero } from '@/components/marketing/Hero';
import { HowItWorks } from '@/components/marketing/HowItWorks';
import { PricingPreview } from '@/components/marketing/PricingPreview';
import { TechStrip } from '@/components/marketing/TechStrip';

export const metadata: Metadata = {
  title: 'Versiona — El Git de tus documentos',
  description:
    'Versiones inmutables, comparación inteligente y aprobación con sellos Ed25519 para tus PDF. Compara dos PDF gratis y crea tu cuenta con 14 días de Pro incluidos.',
};

export default function HomePage() {
  return (
    <main>
      <Hero />
      <HowItWorks />
      <FeaturesGrid />
      <TechStrip />
      <PricingPreview />
      <Faq />
    </main>
  );
}
