'use client';

/** E4 — issue & download certificates for an APPROVED version. */

import { useCallback, useEffect, useState } from 'react';

import { useToast } from '@/components/ui/toast';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import { api } from '@/lib/services/http';

interface CertificateRow {
  public_id: string;
  serial: string;
  issued_by: string;
  created_at: string;
  seals: number;
}

interface CertificatePanelProps {
  versionId: string;
  isApproved: boolean;
  canIssue: boolean;
}

export function CertificatePanel({ versionId, isApproved, canIssue }: CertificatePanelProps) {
  const t = useDict('certificates');
  const common = useDict('common');
  const { toast } = useToast();
  const [rows, setRows] = useState<CertificateRow[]>([]);
  const [isIssuing, setIsIssuing] = useState(false);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get(`versions/${versionId}/certificates/`);
      setRows(data.results);
    } catch {
      setRows([]);
    }
  }, [versionId]);

  useEffect(() => {
    void load();
  }, [load]);

  const issue = async () => {
    setIsIssuing(true);
    try {
      const { data } = await api.post(`versions/${versionId}/certificates/`);
      toast(interpolate(t.issued, { serial: data.serial }), 'success');
      window.open(data.download_url, '_blank', 'noopener');
      void load();
    } catch (err) {
      toast(
        (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
          common.error,
        'error'
      );
    } finally {
      setIsIssuing(false);
    }
  };

  const download = async (certificate: CertificateRow) => {
    const { data } = await api.get(
      `versions/${versionId}/certificates/${certificate.public_id}/download/`
    );
    window.open(data.url, '_blank', 'noopener');
  };

  if (!isApproved && rows.length === 0) return null;

  return (
    <section data-testid="certificate-panel" className="flex flex-col gap-2">
      <h2 className="text-sm font-semibold text-muted-foreground">{t.title}</h2>
      {canIssue && isApproved ? (
        <button
          data-testid="issue-certificate"
          className="self-start rounded-full bg-primary px-4 py-2 text-sm text-primary-foreground disabled:opacity-50"
          disabled={isIssuing}
          onClick={() => void issue()}
          type="button"
        >
          {t.issue}
        </button>
      ) : null}
      {rows.map((certificate) => (
        <article
          key={certificate.public_id}
          data-testid={`certificate-${certificate.serial}`}
          className="rounded-2xl border border-border bg-card p-3 text-sm"
        >
          <p className="font-mono font-medium">{certificate.serial}</p>
          <p className="text-xs text-muted-foreground">
            {certificate.seals} {t.seals} · {t.by} {certificate.issued_by}
          </p>
          <button
            data-testid={`download-${certificate.serial}`}
            className="mt-1 text-xs text-primary underline-offset-2 hover:underline"
            onClick={() => void download(certificate)}
            type="button"
          >
            {t.download}
          </button>
        </article>
      ))}
    </section>
  );
}
