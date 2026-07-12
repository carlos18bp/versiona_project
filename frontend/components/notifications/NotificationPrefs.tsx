'use client';

/** Notification preferences (kit 5 — /settings): event × channel toggles.
 * Mandatory in-app events render disabled: assigned work is never silenced. */

import { useEffect } from 'react';

import { useToast } from '@/components/ui/toast';
import { useDict } from '@/lib/i18n/dictionaries';
import { useLocaleStore } from '@/lib/stores/localeStore';
import { useNotificationStore } from '@/lib/stores/notificationStore';

export function NotificationPrefs() {
  const t = useDict('notifications');
  const { toast } = useToast();
  const locale = useLocaleStore((s) => s.locale);
  const preferences = useNotificationStore((s) => s.preferences);
  const fetchPreferences = useNotificationStore((s) => s.fetchPreferences);
  const updatePreference = useNotificationStore((s) => s.updatePreference);

  useEffect(() => {
    void fetchPreferences();
  }, [fetchPreferences]);

  const toggle = async (eventKey: string, channel: 'in_app' | 'email', enabled: boolean) => {
    const ok = await updatePreference(eventKey, channel, enabled);
    if (!ok) {
      toast(useNotificationStore.getState().error ?? 'Error', 'error');
    }
  };

  return (
    <section data-testid="notification-prefs" className="mt-10">
      <h2 className="text-lg font-semibold">{t.prefsTitle}</h2>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="py-2 pr-4 font-medium"> </th>
              <th className="py-2 pr-4 font-medium">{t.channelInApp}</th>
              <th className="py-2 font-medium">{t.channelEmail}</th>
            </tr>
          </thead>
          <tbody>
            {preferences.map((pref) => (
              <tr key={pref.event_key} className="border-b border-border/60">
                <td className="py-2.5 pr-4">
                  {locale === 'en' ? pref.label_en : pref.label_es}
                  {pref.mandatory_in_app ? (
                    <span className="ml-2 text-xs text-muted-foreground">({t.mandatory})</span>
                  ) : null}
                </td>
                <td className="py-2.5 pr-4">
                  <input
                    data-testid={`pref-${pref.event_key}-in_app`}
                    type="checkbox"
                    aria-label={`${locale === 'en' ? pref.label_en : pref.label_es} — ${t.channelInApp}`}
                    checked={pref.in_app}
                    disabled={pref.mandatory_in_app}
                    onChange={(event) =>
                      void toggle(pref.event_key, 'in_app', event.target.checked)
                    }
                  />
                </td>
                <td className="py-2.5">
                  <input
                    data-testid={`pref-${pref.event_key}-email`}
                    type="checkbox"
                    aria-label={`${locale === 'en' ? pref.label_en : pref.label_es} — ${t.channelEmail}`}
                    checked={pref.email}
                    onChange={(event) =>
                      void toggle(pref.event_key, 'email', event.target.checked)
                    }
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
