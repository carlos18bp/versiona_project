'use client';

import Link from 'next/link';
import { useState } from 'react';
import { Menu, X } from 'lucide-react';

import { LocaleToggle } from '@/components/locale-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';

export function PublicHeader() {
  const t = useDict('marketing');
  const common = useDict('common');
  const [open, setOpen] = useState(false);

  const navLinks = [
    { href: ROUTES.COMPARAR, label: t.navCompare },
    { href: ROUTES.PRECIOS, label: t.navPricing },
    { href: ROUTES.HELP, label: t.navManual },
  ];

  return (
    <header
      data-testid="public-header"
      className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur"
    >
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
        <Link className="font-semibold tracking-tight" href={ROUTES.HOME}>
          Versiona
        </Link>

        <nav className="hidden md:flex items-center gap-2 text-sm">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              className="px-2 py-1 rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              href={link.href}
            >
              {link.label}
            </Link>
          ))}
          <LocaleToggle />
          <ThemeToggle />
          <Link
            className="border border-border rounded-full px-4 py-2 hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            href={ROUTES.SIGN_IN}
          >
            {common.signIn}
          </Link>
          <Link
            className="bg-primary text-primary-foreground rounded-full px-4 py-2 hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            href={ROUTES.SIGN_UP}
          >
            {t.navSignUp}
          </Link>
        </nav>

        <div className="flex md:hidden items-center gap-2">
          <LocaleToggle />
          <ThemeToggle />
          <button
            type="button"
            data-testid="public-nav-toggle"
            aria-label={t.navToggle}
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            onKeyDown={(e) => e.key === 'Escape' && setOpen(false)}
            className="inline-flex h-9 w-9 items-center justify-center rounded-full hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {open ? (
        <nav
          data-testid="public-nav-menu"
          className="md:hidden border-t border-border bg-card px-6 py-4 flex flex-col gap-2 text-sm"
        >
          {navLinks.map((link) => (
            <Link
              key={link.href}
              className="px-2 py-2 rounded hover:bg-accent hover:text-accent-foreground"
              href={link.href}
              onClick={() => setOpen(false)}
            >
              {link.label}
            </Link>
          ))}
          <Link
            className="px-2 py-2 rounded hover:bg-accent hover:text-accent-foreground"
            href={ROUTES.SIGN_IN}
            onClick={() => setOpen(false)}
          >
            {common.signIn}
          </Link>
          <Link
            className="mt-1 bg-primary text-primary-foreground rounded-full px-4 py-2 text-center hover:bg-primary/90"
            href={ROUTES.SIGN_UP}
            onClick={() => setOpen(false)}
          >
            {t.navSignUp}
          </Link>
        </nav>
      ) : null}
    </header>
  );
}
