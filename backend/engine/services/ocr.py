"""
OCR pass for scanned PDFs (docs/plan/05 §3, DP-02 — ocrmypdf + tesseract-spa).

A scanned upload gets a text layer BEFORE sectioning, so the same heading
heuristics and hashing work on it. Confidence gates the trust (DP-03/DP-09):
below `OCR_CONFIDENCE_THRESHOLD` the analysis stays DEGRADED — D5 then forces
coordinator mode (already wired: source_scenario != text_native).
"""

import logging
import statistics
import tempfile
from pathlib import Path

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# ocrmypdf and fontTools narrate every glyph at INFO: keep the worker log
# readable — warnings still surface.
for noisy in ('ocrmypdf', 'fontTools', 'pikepdf'):
    logging.getLogger(noisy).setLevel(logging.WARNING)

OCR_CONFIDENCE_THRESHOLD = 0.75
OCR_LANGUAGE = 'spa'


class OcrError(Exception):
    pass


def run_ocr(data: bytes) -> tuple[bytes, float]:
    """(pdf bytes WITH text layer, mean word confidence 0–1).

    ocrmypdf drives tesseract page by page; confidence comes from a second
    tesseract TSV pass over each page raster (ocrmypdf does not expose it)."""
    import ocrmypdf

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / 'in.pdf'
        dst = Path(tmp) / 'out.pdf'
        src.write_bytes(data)
        try:
            ocrmypdf.ocr(
                src, dst,
                language=OCR_LANGUAGE,
                force_ocr=True,       # rasterized fixtures carry no text at all
                progress_bar=False,
                optimize=0,           # speed over size on the VPS
                output_type='pdf',
            )
        except Exception as exc:  # pragma: no cover - environment specific
            raise OcrError(f'OCR falló: {exc}') from exc
        return dst.read_bytes(), _mean_confidence(data)


def _mean_confidence(data: bytes) -> float:
    """Mean tesseract word confidence over the document's page rasters."""
    import subprocess

    confidences: list[float] = []
    doc = fitz.open(stream=data, filetype='pdf')
    try:
        for page in doc:
            pixmap = page.get_pixmap(dpi=200, colorspace=fitz.csGRAY)
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as raster:
                raster.write(pixmap.tobytes('png'))
                raster_path = raster.name
            try:
                result = subprocess.run(
                    ['tesseract', raster_path, 'stdout', '-l', OCR_LANGUAGE, 'tsv'],
                    capture_output=True, text=True, timeout=120, check=True,
                )
                for line in result.stdout.splitlines()[1:]:
                    columns = line.split('\t')
                    if len(columns) >= 12 and columns[11].strip():
                        conf = float(columns[10])
                        if conf >= 0:  # -1 marks structural rows
                            confidences.append(conf / 100.0)
            finally:
                Path(raster_path).unlink(missing_ok=True)
    finally:
        doc.close()
    if not confidences:
        return 0.0
    return round(statistics.fmean(confidences), 4)


def has_meaningful_text(data: bytes) -> bool:
    doc = fitz.open(stream=data, filetype='pdf')
    try:
        chars = sum(len(page.get_text()) for page in doc)
        return chars / max(doc.page_count, 1) >= 40
    finally:
        doc.close()
