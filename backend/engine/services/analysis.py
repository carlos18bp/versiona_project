"""
Analysis pipeline v1 — native-text PDFs (docs/plan/05 §2–§4, It1 scope).

Pure extraction/sectioning functions operate on bytes and return plain data
(easily asserted against the testdata truth table); persistence lives in
`persist_analysis`. OCR for scanned PDFs joins in It5 (DP-02): until then a
scanned document is detected, sectioned per page (degraded mode) and flagged.

Section identity (D5's ground):
- `stable_key` = slug of the heading WITHOUT its numbering prefix, so
  "7. CONFIDENCIALIDAD" and "6. CONFIDENCIALIDAD" share identity (matching
  step 1 of docs/plan/05 §4). Deduplicated with `-2`, `-3` inside a document.
- Matching steps 1–2 (exact key / exact body hash) run here per new version;
  the full similarity matching (step 3) arrives with the comparison engine
  (It2).

Bounding boxes are normalized 0–1, top-left origin: {page, x0, y0, x1, y1}.
"""

import hashlib
import re
import statistics
import unicodedata
from dataclasses import dataclass, field

import fitz  # PyMuPDF

HEADING_NUMBER_RE = re.compile(r'^\s*(\d+(?:\.\d+)*)[.)]?\s+')
HEADING_KEYWORD_RE = re.compile(
    r'^\s*(cap[ií]tulo|secci[oó]n|anexo|art[ií]culo|cl[aá]usula)\s+\w+', re.IGNORECASE
)
MAX_HEADING_CHARS = 90
PREAMBLE_KEY = '__preamble__'


class InvalidPdfError(Exception):
    """Corrupt or non-PDF content (C1-E02)."""


class EncryptedPdfError(Exception):
    """Password-protected PDF (C1-E01)."""


@dataclass
class ExtractedSection:
    heading: str
    level: int
    order_index: int
    page_start: int
    page_end: int
    body_parts: list = field(default_factory=list)
    bboxes: list = field(default_factory=list)

    @property
    def body_text(self) -> str:
        return normalize_text(' '.join(self.body_parts))


def normalize_text(text: str) -> str:
    """NFC + collapsed whitespace + de-hyphenated line breaks (docs/plan/05 §6.2):
    hash equality must survive re-rendering/compression."""
    text = unicodedata.normalize('NFC', text or '')
    text = re.sub(r'(\w)-\s+(\w)', r'\1\2', text)
    return re.sub(r'\s+', ' ', text).strip()


def content_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode('utf-8')).hexdigest()


def stable_key_for(heading: str, taken: set) -> str:
    from django.utils.text import slugify

    stripped = HEADING_NUMBER_RE.sub('', normalize_text(heading))
    base = slugify(stripped)[:200] or 'seccion'
    key = base
    suffix = 1
    while key in taken:
        suffix += 1
        key = f'{base}-{suffix}'
    taken.add(key)
    return key


def open_pdf(data: bytes) -> fitz.Document:
    try:
        doc = fitz.open(stream=data, filetype='pdf')
    except Exception as exc:
        raise InvalidPdfError(str(exc)) from exc
    if doc.needs_pass:
        raise EncryptedPdfError('PDF is password-protected')
    if doc.page_count == 0:
        raise InvalidPdfError('PDF has no pages')
    return doc


def detect_scenario(doc: fitz.Document) -> str:
    """`text_native` when real text exists; `scanned_ocr` otherwise."""
    chars = sum(len(page.get_text().strip()) for page in doc)
    return 'text_native' if chars / max(doc.page_count, 1) >= 40 else 'scanned_ocr'


def _lines_with_style(doc: fitz.Document):
    """Yield (page_index, text, max_font_size, is_bold, normalized_bbox)."""
    for page_index, page in enumerate(doc):
        width, height = page.rect.width or 1, page.rect.height or 1
        for block in page.get_text('dict')['blocks']:
            if block.get('type') != 0:
                continue
            for line in block.get('lines', []):
                spans = line.get('spans', [])
                text = ''.join(span['text'] for span in spans).strip()
                if not text:
                    continue
                size = max(span['size'] for span in spans)
                bold = any(span['flags'] & 2 ** 4 for span in spans)
                x0, y0, x1, y1 = line['bbox']
                bbox = {
                    'page': page_index + 1,
                    'x0': round(x0 / width, 4),
                    'y0': round(y0 / height, 4),
                    'x1': round(x1 / width, 4),
                    'y1': round(y1 / height, 4),
                }
                yield page_index + 1, text, size, bold, bbox


def _is_heading(text: str, size: float, bold: bool, size_p85: float) -> bool:
    if len(text) > MAX_HEADING_CHARS:
        return False
    if HEADING_NUMBER_RE.match(text) and (bold or size >= size_p85):
        return True
    if HEADING_KEYWORD_RE.match(text) and (bold or size >= size_p85):
        return True
    return bool(bold and size >= size_p85 and len(text) < 60)


def _heading_level(text: str) -> int:
    match = HEADING_NUMBER_RE.match(text)
    if match and '.' in match.group(1):
        return 2
    return 1


def extract_sections(doc: fitz.Document) -> tuple[list[ExtractedSection], bool]:
    """Returns (sections, degraded). Fallback (DP-09): fewer than 2 detected
    headings ⇒ one section per page + degraded mode."""
    lines = list(_lines_with_style(doc))
    sizes = [size for _, _, size, _, _ in lines] or [10.0]
    size_p85 = statistics.quantiles(sizes, n=20)[16] if len(sizes) > 1 else sizes[0]

    sections: list[ExtractedSection] = []
    current: ExtractedSection | None = None
    order = 0

    for page, text, size, bold, bbox in lines:
        if _is_heading(text, size, bold, size_p85):
            current = ExtractedSection(
                heading=normalize_text(text),
                level=_heading_level(text),
                order_index=order,
                page_start=page,
                page_end=page,
                bboxes=[bbox],
            )
            sections.append(current)
            order += 1
            continue
        if current is None:
            current = ExtractedSection(
                heading='Preámbulo', level=1, order_index=order,
                page_start=page, page_end=page, bboxes=[],
            )
            current.is_preamble = True
            sections.append(current)
            order += 1
        current.body_parts.append(text)
        current.bboxes.append(bbox)
        current.page_end = page

    real_headings = [s for s in sections if not getattr(s, 'is_preamble', False)]
    if len(real_headings) < 2:
        return _page_fallback_sections(doc), True
    return sections, False


def _page_fallback_sections(doc: fitz.Document) -> list[ExtractedSection]:
    sections = []
    for page_index, page in enumerate(doc):
        section = ExtractedSection(
            heading=f'Página {page_index + 1}',
            level=1,
            order_index=page_index,
            page_start=page_index + 1,
            page_end=page_index + 1,
            bboxes=[{'page': page_index + 1, 'x0': 0.0, 'y0': 0.0, 'x1': 1.0, 'y1': 1.0}],
        )
        section.body_parts.append(page.get_text())
        sections.append(section)
    return sections


def render_thumbnail(doc: fitz.Document, width: int = 320) -> bytes:
    """First-page PNG thumbnail (kit 1). Works for scanned PDFs too."""
    page = doc[0]
    zoom = width / (page.rect.width or 1)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    return pix.tobytes('png')


def analyze_bytes(data: bytes) -> dict:
    """Pure pipeline: bytes → structured analysis (asserted vs truth table)."""
    doc = open_pdf(data)
    try:
        scenario = detect_scenario(doc)
        sections, degraded = extract_sections(doc)
        taken: set = set()
        payload_sections = []
        for section in sections:
            body = section.body_text
            payload_sections.append({
                'stable_key': stable_key_for(section.heading, taken),
                'heading': section.heading,
                'heading_hash': content_hash(section.heading),
                'body_hash': content_hash(body),
                'normalized_text': body,
                'level': section.level,
                'order_index': section.order_index,
                'page_start': section.page_start,
                'page_end': section.page_end,
                'bboxes': section.bboxes,
                'char_count': len(body),
            })
        return {
            'scenario': scenario,
            'degraded': degraded or scenario == 'scanned_ocr',
            'page_count': doc.page_count,
            'sections': payload_sections,
            'thumbnail_png': render_thumbnail(doc),
        }
    finally:
        doc.close()
