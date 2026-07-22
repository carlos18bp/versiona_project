'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { ChevronRight } from 'lucide-react';

import { NotificationPrefs } from '@/components/notifications/NotificationPrefs';
import { SecuritySection } from '@/components/security/SecuritySection';
import { AsyncBoundary } from '@/components/ui/AsyncBoundary';
import { useToast } from '@/components/ui/toast';
import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';
import { useRequireAuth } from '@/lib/hooks/useRequireAuth';
import { useProfileStore } from '@/lib/stores/profileStore';
import type { Profile } from '@/lib/types';

const COMMON_TIMEZONES = [
  'America/Bogota',
  'America/Mexico_City',
  'America/Lima',
  'America/Argentina/Buenos_Aires',
  'America/Santiago',
  'Europe/Madrid',
  'UTC',
];

export default function SettingsPage() {
  const { isAuthenticated } = useRequireAuth();
  const t = useDict('settings');
  const common = useDict('common');
  const { toast } = useToast();
  const profile = useProfileStore((s) => s.profile);
  const isLoading = useProfileStore((s) => s.isLoading);
  const isSaving = useProfileStore((s) => s.isSaving);
  const error = useProfileStore((s) => s.error);
  const fetchProfile = useProfileStore((s) => s.fetchProfile);
  const updateProfile = useProfileStore((s) => s.updateProfile);
  const [form, setForm] = useState<Partial<Profile>>({});

  useEffect(() => {
    if (isAuthenticated) void fetchProfile();
  }, [isAuthenticated, fetchProfile]);

  useEffect(() => {
    if (profile) setForm(profile);
  }, [profile]);

  if (!isAuthenticated) return null;

  const set = (key: keyof Profile, value: string) =>
    setForm((current) => ({ ...current, [key]: value }));

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    const ok = await updateProfile({
      first_name: form.first_name,
      last_name: form.last_name,
      phone: form.phone,
      language: form.language,
      timezone: form.timezone,
    });
    toast(ok ? common.saved : (useProfileStore.getState().error ?? common.error), ok ? 'success' : 'error');
  };

  return (
    <main className="mx-auto max-w-xl px-6 py-10">
      <h1 className="text-2xl font-semibold">{t.title}</h1>
      <Link
        data-testid="settings-usage-link"
        className="mt-3 flex items-center justify-between rounded-2xl border border-border bg-card px-4 py-3 text-sm hover:bg-accent hover:text-accent-foreground"
        href={ROUTES.ORG_USAGE}
      >
        {common.planUsage}
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </Link>
      <h2 className="mt-6 text-sm text-muted-foreground">{t.profile}</h2>

      <div className="mt-6">
        <AsyncBoundary
          isLoading={isLoading && !profile}
          error={!profile ? error : null}
          onRetry={() => void fetchProfile()}
          retryLabel={common.retry}
        >
          <form className="flex flex-col gap-4" onSubmit={submit}>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="block text-sm">
                <span className="text-muted-foreground">{t.firstName}</span>
                <input
                  data-testid="settings-first-name"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2"
                  value={form.first_name ?? ''}
                  onChange={(event) => set('first_name', event.target.value)}
                />
              </label>
              <label className="block text-sm">
                <span className="text-muted-foreground">{t.lastName}</span>
                <input
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2"
                  value={form.last_name ?? ''}
                  onChange={(event) => set('last_name', event.target.value)}
                />
              </label>
            </div>
            <label className="block text-sm">
              <span className="text-muted-foreground">{t.phone}</span>
              <input
                className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2"
                value={form.phone ?? ''}
                onChange={(event) => set('phone', event.target.value)}
              />
            </label>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="block text-sm">
                <span className="text-muted-foreground">{t.language}</span>
                <select
                  data-testid="settings-language"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2"
                  value={form.language ?? 'es'}
                  onChange={(event) => set('language', event.target.value)}
                >
                  <option value="es">{t.languageEs}</option>
                  <option value="en">{t.languageEn}</option>
                </select>
              </label>
              <label className="block text-sm">
                <span className="text-muted-foreground">{t.timezone}</span>
                <select
                  data-testid="settings-timezone"
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2"
                  value={form.timezone ?? 'America/Bogota'}
                  onChange={(event) => set('timezone', event.target.value)}
                >
                  {COMMON_TIMEZONES.map((zone) => (
                    <option key={zone} value={zone}>
                      {zone}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button
              data-testid="settings-save"
              className="self-start rounded-full bg-primary px-5 py-2.5 text-sm text-primary-foreground disabled:opacity-50"
              disabled={isSaving}
              type="submit"
            >
              {common.save}
            </button>
          </form>
        </AsyncBoundary>
      </div>

      <SecuritySection />
      <NotificationPrefs />
    </main>
  );
}
