'use client';

import { FileCheck, Lock, ScanText, Signature } from 'lucide-react';

import { useDict } from '@/lib/i18n/dictionaries';

export function TechStrip() {
  const t = useDict('marketing');

  const items = [
    { Icon: Signature, label: t.tech1 },
    { Icon: Lock, label: t.tech2 },
    { Icon: FileCheck, label: t.tech3 },
    { Icon: ScanText, label: t.tech4 },
  ];

  return (
    <section data-testid="tech-strip" className="max-w-6xl mx-auto px-6 py-12">
      <p className="text-sm font-medium text-muted-foreground">{t.techTitle}</p>
      <ul className="mt-4 flex flex-wrap gap-x-8 gap-y-3">
        {items.map(({ Icon, label }) => (
          <li key={label} className="flex items-center gap-2 text-sm">
            <Icon className="h-4 w-4 text-primary" />
            {label}
          </li>
        ))}
      </ul>
    </section>
  );
}
