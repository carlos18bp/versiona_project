'use client';

import Link from 'next/link';

import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { ROUTES } from '@/lib/constants';
import { useDict } from '@/lib/i18n/dictionaries';
import { useUpgradeDialogStore } from '@/lib/stores/upgradeDialogStore';

export function UpgradeDialog() {
  const t = useDict('billing');
  const isOpen = useUpgradeDialogStore((s) => s.isOpen);
  const detail = useUpgradeDialogStore((s) => s.detail);
  const hide = useUpgradeDialogStore((s) => s.hide);

  return (
    <Modal open={isOpen} onClose={hide} title={t.upgradeTitle}>
      <div data-testid="upgrade-dialog" className="flex flex-col gap-3">
        <p>
          <StatusBadge variant="draft">{t.locked}</StatusBadge>
        </p>
        {detail ? <p className="text-sm">{detail}</p> : null}
        <p className="text-sm text-muted-foreground">{t.upgradeDialogBody}</p>
        <div className="mt-2 flex flex-wrap items-center gap-3">
          <Link
            data-testid="upgrade-dialog-plans"
            className="rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground hover:bg-primary/90"
            href={ROUTES.PRECIOS}
            onClick={hide}
          >
            {t.upgradeCta}
          </Link>
          <a
            data-testid="upgrade-dialog-contact"
            className="text-sm text-muted-foreground hover:text-foreground underline"
            href="mailto:hola@versiona.app?subject=Plan%20Pro"
          >
            {t.contactUs}
          </a>
        </div>
      </div>
    </Modal>
  );
}
