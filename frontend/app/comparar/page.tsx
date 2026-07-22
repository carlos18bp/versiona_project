'use client';

import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

import { PublicCompareCta } from '@/components/public-compare/PublicCompareCta';
import { PublicDropzone } from '@/components/public-compare/PublicDropzone';
import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import {
  PUBLIC_COMPARE_MAX_MB,
  PUBLIC_COMPARE_MAX_PAGES,
  PUBLIC_COMPARE_TTL_HOURS,
  usePublicCompareStore,
} from '@/lib/stores/publicCompareStore';

export default function CompararPage() {
  const router = useRouter();
  const t = useDict('publicCompare');
  const slotA = usePublicCompareStore((s) => s.slotA);
  const slotB = usePublicCompareStore((s) => s.slotB);
  const phase = usePublicCompareStore((s) => s.phase);
  const progress = usePublicCompareStore((s) => s.progress);
  const errorKey = usePublicCompareStore((s) => s.errorKey);
  const submit = usePublicCompareStore((s) => s.submit);
  const reset = usePublicCompareStore((s) => s.reset);

  useEffect(() => {
    reset();
  }, [reset]);

  const busy = phase === 'uploading' || phase === 'processing';

  const errorMessage =
    errorKey &&
    interpolate(
      {
        missingFiles: t.errorMissingFiles,
        notPdf: t.errorNotPdf,
        tooBig: t.errorTooBig,
        tooManyPages: t.errorTooManyPages,
        scannedNeedsOcr: t.errorScannedNeedsOcr,
        encrypted: t.errorEncrypted,
        invalid: t.errorInvalid,
        rateLimited: t.errorRateLimited,
        genericFailed: t.errorGenericFailed,
        expired: t.errorExpired,
      }[errorKey],
      { mb: PUBLIC_COMPARE_MAX_MB, pages: PUBLIC_COMPARE_MAX_PAGES }
    );

  const start = async () => {
    const publicId = await submit();
    if (publicId) router.push(`/comparar/${publicId}`);
  };

  return (
    <>
      <main className="max-w-4xl mx-auto px-6 py-14">
        <h1 className="text-3xl sm:text-4xl font-bold tracking-tight">{t.title}</h1>
        <p className="mt-3 text-muted-foreground">{t.subtitle}</p>

        <div className="mt-8">
          <PublicDropzone />
        </div>

        {errorMessage ? (
          <p
            role="alert"
            data-testid="public-compare-error"
            className="mt-4 rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive"
          >
            {errorMessage}
          </p>
        ) : null}

        <div className="mt-6 flex items-center gap-4">
          <button
            type="button"
            data-testid="public-compare-submit"
            className="rounded-full bg-primary text-primary-foreground px-6 py-3 hover:bg-primary/90 disabled:opacity-50"
            disabled={!slotA || !slotB || busy}
            onClick={() => void start()}
          >
            {t.compareCta}
          </button>
          {phase === 'uploading' ? (
            <p className="text-sm text-muted-foreground" role="status">
              {interpolate(t.uploading, { progress })}
            </p>
          ) : null}
          {phase === 'processing' ? (
            <p className="text-sm text-muted-foreground" role="status">
              {t.processing}
            </p>
          ) : null}
        </div>

        <p className="mt-10 text-xs text-muted-foreground">
          {interpolate(t.privacyNote, { hours: PUBLIC_COMPARE_TTL_HOURS })}
        </p>
      </main>
      <PublicCompareCta />
    </>
  );
}
