'use client';

/**
 * PDF viewer v1 (docs/plan/04 §3 — react-pdf, client-only). Renders from a
 * presigned URL or a local File (LocalPdfPreview). Page virtualization and
 * overlay layers (observations/diff) join in It2–It4.
 */

import { useState } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';

import 'react-pdf/dist/Page/AnnotationLayer.css';
import 'react-pdf/dist/Page/TextLayer.css';

import { Skeleton } from '@/components/ui/Skeleton';

pdfjs.GlobalWorkerOptions.workerSrc = new URL(
  'pdfjs-dist/build/pdf.worker.min.mjs',
  import.meta.url
).toString();

interface PdfViewerProps {
  file: string | File;
  maxPages?: number;
  width?: number;
  onLoaded?: (pages: number) => void;
}

export function PdfViewer({ file, maxPages, width = 760, onLoaded }: PdfViewerProps) {
  const [pageCount, setPageCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  if (error) {
    return (
      <div
        data-testid="pdf-error"
        className="rounded-2xl border border-destructive/30 bg-destructive/5 p-6 text-sm text-destructive"
      >
        {error}
      </div>
    );
  }

  const pagesToRender = maxPages ? Math.min(pageCount, maxPages) : pageCount;

  return (
    <div data-testid="pdf-viewer" className="flex flex-col items-center gap-4">
      <Document
        file={file}
        loading={<Skeleton className="h-[480px] w-full max-w-[760px]" />}
        onLoadSuccess={(doc) => {
          setPageCount(doc.numPages);
          onLoaded?.(doc.numPages);
        }}
        onLoadError={(err) => setError(err.message)}
      >
        {Array.from({ length: pagesToRender }, (_, index) => (
          <div key={index} className="mb-4 overflow-hidden rounded-xl border border-border shadow-sm">
            <Page
              pageNumber={index + 1}
              width={width}
              renderAnnotationLayer={false}
            />
          </div>
        ))}
      </Document>
      {maxPages && pageCount > maxPages ? (
        <p className="text-xs text-muted-foreground">
          +{pageCount - maxPages} páginas más en el documento completo
        </p>
      ) : null}
    </div>
  );
}
