'use client';

/** A2 — the invitation landing: public state, then accept (exact email). */

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Skeleton } from '@/components/ui/Skeleton';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { api } from '@/lib/services/http';
import { useAuthStore } from '@/lib/stores/authStore';

interface InviteState {
  status: 'pending' | 'accepted' | 'revoked' | 'expired';
  email: string;
  role: string;
  project_name: string | null;
  org_name: string;
  invited_by: string;
}

export default function InvitePage() {
  const params = useParams<{ token: string }>();
  const router = useRouter();
  const t = useDict('invitations');
  const common = useDict('common');
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const userEmail = useAuthStore((s) => s.user?.email ?? null);
  const [state, setState] = useState<InviteState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAccepting, setIsAccepting] = useState(false);

  useEffect(() => {
    void api
      .get<InviteState>(`invitations/${params.token}/`)
      .then(({ data }) => setState(data))
      .catch(() => setError(common.error));
  }, [params.token, common.error]);

  const accept = async () => {
    setIsAccepting(true);
    setError(null);
    try {
      const { data } = await api.post(`invitations/${params.token}/accept/`);
      router.push(data.landing ?? '/projects');
    } catch (err) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
          common.error
      );
      setIsAccepting(false);
    }
  };

  if (!state && !error) {
    return (
      <main className="mx-auto max-w-lg px-6 py-16">
        <Skeleton className="h-48 w-full" />
      </main>
    );
  }

  return (
    <main
      data-testid="invite-landing"
      className="mx-auto flex max-w-lg flex-col items-center px-6 py-16 text-center"
    >
      <h1 className="text-2xl font-semibold">{t.landingTitle}</h1>
      {state ? (
        <>
          <p className="mt-3 text-muted-foreground">
            {interpolate(t.landingBody, {
              invited_by: state.invited_by,
              role: state.role,
              project_name: state.project_name ?? state.org_name,
            })}
          </p>

          {state.status === 'expired' ? (
            <p role="alert" className="mt-4 text-destructive">{t.expired}</p>
          ) : state.status === 'accepted' ? (
            <p role="alert" className="mt-4 text-muted-foreground">{t.used}</p>
          ) : state.status === 'revoked' ? (
            <p role="alert" className="mt-4 text-destructive">{t.revokedMsg}</p>
          ) : !isAuthenticated ? (
            <div className="mt-6 flex flex-col items-center gap-3">
              <p className="text-sm text-muted-foreground">
                {interpolate(t.needAccount, { email: state.email })}
              </p>
              <div className="flex gap-2">
                <Link
                  className="rounded-full border border-border px-5 py-2.5 text-sm hover:bg-accent"
                  href={`/sign-in?next=/invite/${params.token}`}
                >
                  {common.signIn}
                </Link>
                <Link
                  className="rounded-full bg-primary px-5 py-2.5 text-sm text-primary-foreground"
                  href={`/sign-up?next=/invite/${params.token}`}
                >
                  {common.signUp}
                </Link>
              </div>
            </div>
          ) : userEmail && userEmail.toLowerCase() !== state.email.toLowerCase() ? (
            <p role="alert" className="mt-4 text-destructive">
              {interpolate(t.wrongAccount, { email: state.email })}
            </p>
          ) : (
            <button
              data-testid="accept-invitation"
              className="mt-6 rounded-full bg-primary px-6 py-3 text-primary-foreground disabled:opacity-60"
              disabled={isAccepting}
              onClick={() => void accept()}
              type="button"
            >
              {t.accept}
            </button>
          )}
        </>
      ) : null}
      {error ? (
        <p role="alert" className="mt-4 text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </main>
  );
}
