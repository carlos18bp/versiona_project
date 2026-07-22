'use client';

/**
 * Two-slot anonymous dropzone (antes / después). Dropping two files at once
 * fills both slots; each slot also has its own picker. Micro-patterns
 * (value-reset trick, drag counter) mirror versions/UploadDropzone.
 */
import { ArrowUpDown, FileText, X } from 'lucide-react';
import { useRef, useState, type DragEvent } from 'react';

import { interpolate, useDict } from '@/lib/i18n/dictionaries';
import {
  PUBLIC_COMPARE_MAX_MB,
  PUBLIC_COMPARE_MAX_PAGES,
  usePublicCompareStore,
} from '@/lib/stores/publicCompareStore';

function formatSize(bytes: number) {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function Slot({ slot, label }: { slot: 'a' | 'b'; label: string }) {
  const t = useDict('publicCompare');
  const file = usePublicCompareStore((s) => (slot === 'a' ? s.slotA : s.slotB));
  const setSlot = usePublicCompareStore((s) => s.setSlot);
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="rounded-2xl border border-dashed border-border bg-card p-4 flex flex-col gap-2">
      <p className="text-xs font-medium text-muted-foreground">{label}</p>
      {file ? (
        <div className="flex items-center justify-between gap-2 text-sm">
          <span className="flex items-center gap-2 min-w-0">
            <FileText className="h-4 w-4 shrink-0 text-primary" />
            <span className="truncate" data-testid={`public-file-name-${slot}`}>
              {file.name}
            </span>
            <span className="shrink-0 text-xs text-muted-foreground">
              {formatSize(file.size)}
            </span>
          </span>
          <button
            type="button"
            aria-label={t.remove}
            data-testid={`public-file-remove-${slot}`}
            className="rounded p-1 text-muted-foreground hover:bg-accent hover:text-accent-foreground"
            onClick={() => setSlot(slot, null)}
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <button
          type="button"
          className="rounded-full border border-border px-4 py-2 text-sm hover:bg-accent hover:text-accent-foreground self-start"
          onClick={() => inputRef.current?.click()}
        >
          {t.pickFile}
        </button>
      )}
      <input
        ref={inputRef}
        data-testid={`public-file-${slot}`}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        onChange={(event) => {
          const picked = event.target.files?.[0] ?? null;
          if (picked) setSlot(slot, picked);
          event.target.value = ''; // allow re-picking the same file
        }}
      />
    </div>
  );
}

export function PublicDropzone() {
  const t = useDict('publicCompare');
  const setSlot = usePublicCompareStore((s) => s.setSlot);
  const slotA = usePublicCompareStore((s) => s.slotA);
  const slotB = usePublicCompareStore((s) => s.slotB);
  const swap = usePublicCompareStore((s) => s.swap);
  const [dragging, setDragging] = useState(0);

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(0);
    const files = Array.from(event.dataTransfer.files ?? []).slice(0, 2);
    if (files.length === 0) return;
    if (files.length === 2) {
      setSlot('a', files[0]);
      setSlot('b', files[1]);
      return;
    }
    if (!slotA) setSlot('a', files[0]);
    else setSlot('b', files[0]);
  };

  return (
    <div
      data-testid="public-dropzone"
      className={`rounded-3xl border-2 border-dashed p-5 transition-colors ${
        dragging > 0 ? 'border-primary bg-primary/5' : 'border-border bg-muted/30'
      }`}
      onDragEnter={(e) => {
        e.preventDefault();
        setDragging((v) => v + 1);
      }}
      onDragLeave={(e) => {
        e.preventDefault();
        setDragging((v) => Math.max(0, v - 1));
      }}
      onDragOver={(e) => e.preventDefault()}
      onDrop={onDrop}
    >
      <p className="text-sm text-muted-foreground text-center">{t.dropHint}</p>
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-[1fr_auto_1fr] items-center gap-3">
        <Slot slot="a" label={t.slotALabel} />
        <button
          type="button"
          aria-label={t.swap}
          data-testid="public-swap"
          className="justify-self-center rounded-full border border-border p-2 hover:bg-accent hover:text-accent-foreground disabled:opacity-40"
          disabled={!slotA && !slotB}
          onClick={swap}
        >
          <ArrowUpDown className="h-4 w-4 sm:rotate-90" />
        </button>
        <Slot slot="b" label={t.slotBLabel} />
      </div>
      <p className="mt-3 text-center text-xs text-muted-foreground">
        {interpolate(t.requirements, {
          mb: PUBLIC_COMPARE_MAX_MB,
          pages: PUBLIC_COMPARE_MAX_PAGES,
        })}
      </p>
    </div>
  );
}
