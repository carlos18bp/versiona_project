'use client';

import Link from 'next/link';

import { LocaleToggle } from '@/components/locale-toggle';
import { ThemeToggle } from '@/components/theme-toggle';
import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';

export function PublicFooter() {
  const t = useDict('marketing');
  const common = useDict('common');

  return (
    <footer data-testid="public-footer" className="border-t border-border mt-16">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
          <div>
            <p className="text-sm font-semibold">{t.footerProduct}</p>
            <ul className="mt-3 flex flex-col gap-2 text-sm text-muted-foreground">
              <li>
                <Link className="hover:text-foreground" href={ROUTES.COMPARAR}>
                  {t.navCompare}
                </Link>
              </li>
              <li>
                <Link className="hover:text-foreground" href={ROUTES.PRECIOS}>
                  {t.navPricing}
                </Link>
              </li>
              <li>
                <Link className="hover:text-foreground" href={ROUTES.HELP}>
                  {t.navManual}
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold">{t.footerAccount}</p>
            <ul className="mt-3 flex flex-col gap-2 text-sm text-muted-foreground">
              <li>
                <Link className="hover:text-foreground" href={ROUTES.SIGN_UP}>
                  {common.signUp}
                </Link>
              </li>
              <li>
                <Link className="hover:text-foreground" href={ROUTES.SIGN_IN}>
                  {common.signIn}
                </Link>
              </li>
            </ul>
          </div>
          <div>
            <p className="text-sm font-semibold">{t.footerProject}</p>
            <ul className="mt-3 flex flex-col gap-2 text-sm text-muted-foreground">
              <li>
                <a className="hover:text-foreground" href="mailto:hola@versiona.app">
                  {t.footerContact}
                </a>
              </li>
              <li className="flex items-center gap-1">
                <LocaleToggle />
                <ThemeToggle />
              </li>
            </ul>
          </div>
        </div>
        <p className="mt-10 text-sm text-muted-foreground">{t.footerCopyright}</p>
      </div>
    </footer>
  );
}
