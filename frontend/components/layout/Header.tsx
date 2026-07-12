'use client';

import Link from 'next/link';
import { useEffect } from 'react';

import { NotificationBell } from '@/components/notifications/NotificationBell';
import { ThemeToggle } from '@/components/theme-toggle';
import { ROUTES } from '@/lib/constants';
import { useAuthStore } from '@/lib/stores/authStore';
import { useOrgStore } from '@/lib/stores/orgStore';
import { useDict } from '@/lib/i18n/dictionaries';

export default function Header() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const signOut = useAuthStore((s) => s.signOut);
  const t = useDict('common');
  const orgs = useOrgStore((s) => s.orgs);
  const fetchOrgs = useOrgStore((s) => s.fetchOrgs);

  useEffect(() => {
    if (isAuthenticated && orgs.length === 0) void fetchOrgs();
  }, [isAuthenticated, orgs.length, fetchOrgs]);

  // The trash is an org-admin surface (docs/plan/03 §3): hide it for everyone
  // else instead of letting them walk into a 403.
  const canSeeTrash = orgs.some((org) => org.role === 'owner' || org.role === 'admin');

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-card/80 backdrop-blur">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between gap-4">
        <Link className="font-semibold tracking-tight" href="/">
          Versiona
        </Link>

        <nav className="flex items-center gap-2 sm:gap-4 text-sm">
          <Link
            className="px-2 py-1 rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            href={ROUTES.HELP}
          >
            {t.help}
          </Link>

          <ThemeToggle />

          {isAuthenticated ? (
            <>
              <Link
                className="px-2 py-1 rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                href="/projects"
              >{t.panel}</Link>
              {canSeeTrash ? (
                <Link
                  className="px-2 py-1 rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  href="/org/trash"
                >
                  {t.trash}
                </Link>
              ) : null}
              <Link
                className="px-2 py-1 rounded hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                href="/settings"
              >{t.settings}</Link>
              <NotificationBell />
              <button
                className="border border-border rounded-full px-4 py-2 hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                onClick={signOut}
                type="button"
              >{t.signOut}</button>
            </>
          ) : (
            <>
              <Link
                className="border border-border rounded-full px-4 py-2 hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                href={ROUTES.SIGN_IN}
              >{t.signIn}</Link>
              <Link
                className="bg-primary text-primary-foreground rounded-full px-4 py-2 hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                href={ROUTES.SIGN_UP}
              >{t.signUp}</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
