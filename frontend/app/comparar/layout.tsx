import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Comparar dos PDF gratis — Versiona',
  description:
    'Sube dos PDF y mira qué cambió, sección por sección. Sin cuenta y sin instalar nada.',
};

export default function CompararLayout({ children }: { children: React.ReactNode }) {
  return children;
}
