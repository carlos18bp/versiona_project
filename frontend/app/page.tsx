'use client';

import Link from 'next/link';

import { ROUTES } from '@/lib/constants';

const PILLARS = [
  {
    label: 'Versiones',
    text: 'Cada carga es una versión inmutable, con autor, fecha y mensaje. La historia de tu documento queda a salvo.',
  },
  {
    label: 'Comparación',
    text: 'Qué cambió entre dos versiones, resaltado sobre el documento. Nadie vuelve a releer desde cero.',
  },
  {
    label: 'Sellos',
    text: 'Aprobaciones amarradas a la versión exacta y a las secciones revisadas. Si algo cambia, solo se revisa lo que cambió.',
  },
];

export default function HomePage() {
  return (
    <main>
      <section className="border-b border-border bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-background via-muted to-background">
        <div className="max-w-6xl mx-auto px-6 py-20">
          <div className="max-w-3xl">
            <p className="inline-flex items-center text-xs font-medium text-foreground bg-card border border-border rounded-full px-3 py-1">
              Control de versiones para documentos
            </p>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mt-4">
              El Git de tus documentos
            </h1>
            <p className="mt-4 text-muted-foreground max-w-2xl">
              Versiones, comparación y aprobación con sello para el mundo que trabaja en PDF.
              Se acabó el final_v3_AHORA_SI.pdf.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                className="bg-primary text-primary-foreground rounded-full px-5 py-3 hover:bg-primary/90 shadow-sm"
                href={ROUTES.SIGN_UP}
              >
                Crear cuenta gratis
              </Link>
              <Link
                className="border border-border rounded-full px-5 py-3 hover:bg-accent hover:text-accent-foreground shadow-sm"
                href={ROUTES.SIGN_IN}
              >
                Iniciar sesión
              </Link>
            </div>
          </div>

          <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-3">
            {PILLARS.map((pillar) => (
              <div key={pillar.label} className="rounded-2xl bg-card border border-border p-5">
                <p className="text-xs text-muted-foreground">{pillar.label}</p>
                <p className="mt-2 text-sm text-foreground">{pillar.text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </main>
  );
}
