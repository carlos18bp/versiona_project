'use client';

/** A1 — the wizard: name your org, we seed the sample, you land on a WORKING
 * comparison (metric S1: value in under 5 minutes). */

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Skeleton } from '@/components/ui/Skeleton';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { api } from '@/lib/services/http';

interface OnboardingState {
  status: 'no_org' | 'pending' | 'done';
  org_name?: string;
  wow_link?: string | null;
}

export default function OnboardingPage() {
  const { isAuthenticated } = useRequireAuth();
  const router = useRouter();
  const t = useDict('onboarding');
  const common = useDict('common');
  const [state, setState] = useState<OnboardingState | null>(null);
  const [orgName, setOrgName] = useState('');
  const [isSeeding, setIsSeeding] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) return;
    void api
      .get<OnboardingState>('me/onboarding/')
      .then(({ data }) => {
        setState(data);
        if (data.org_name) setOrgName(data.org_name);
      })
      .catch(() => setError(common.error));
  }, [isAuthenticated, common.error]);

  if (!isAuthenticated) return null;

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsSeeding(true);
    setError(null);
    try {
      const { data } = await api.post<OnboardingState>('me/onboarding/', {
        org_name: orgName.trim(),
      });
      if (data.wow_link) {
        router.push(data.wow_link);
      } else {
        router.push('/projects');
      }
    } catch (err) {
      setError(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
          common.error
      );
      setIsSeeding(false);
    }
  };

  return (
    <main className="mx-auto flex max-w-lg flex-col items-center px-6 py-16 text-center">
      {state === null && !error ? (
        <Skeleton className="h-48 w-full" />
      ) : state?.status === 'done' ? (
        <div data-testid="onboarding-done">
          <h1 className="text-3xl font-semibold">{t.wowReady}</h1>
          <p className="mt-2 text-muted-foreground">{t.wowBody}</p>
          <button
            data-testid="go-wow"
            className="mt-6 rounded-full bg-primary px-6 py-3 text-primary-foreground"
            onClick={() => router.push(state.wow_link ?? '/projects')}
            type="button"
          >
            {t.goWow}
          </button>
        </div>
      ) : (
        <form data-testid="onboarding-form" className="w-full" onSubmit={submit}>
          <h1 className="text-3xl font-semibold">{t.title}</h1>
          <p className="mt-2 text-muted-foreground">{t.subtitle}</p>
          <input
            data-testid="onboarding-org-name"
            className="mt-6 w-full rounded-xl border border-border bg-background px-4 py-3 text-center text-lg"
            placeholder={t.orgName}
            value={orgName}
            onChange={(event) => setOrgName(event.target.value)}
            autoFocus
          />
          {error ? (
            <p role="alert" className="mt-2 text-sm text-destructive">
              {error}
            </p>
          ) : null}
          <button
            data-testid="onboarding-submit"
            className="mt-4 w-full rounded-full bg-primary px-6 py-3 text-primary-foreground disabled:opacity-60"
            disabled={isSeeding || !orgName.trim()}
            type="submit"
          >
            {isSeeding ? t.seeding : t.cta}
          </button>
        </form>
      )}
    </main>
  );
}
