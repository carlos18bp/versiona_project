#!/usr/bin/env python3
"""
Deterministic PDF fixture generator for Versiona (docs/plan/06 §6).

Produces byte-reproducible PDFs consumed by pytest, Playwright and
`create_fake_data` (the A1 sample project). NEVER edit the generated PDFs by
hand: change this script and regenerate in a PR that also updates the truth
table in testdata/README.md.

Usage (from the repo root, with the backend venv):
    backend/venv/bin/python testdata/generate_pdfs.py

Fixtures:
- contrato_v1.pdf      native text, 8 numbered sections (the baseline)
- contrato_v2.pdf      the documented re-delivery (truth table in README.md)
- escaneado_v1.pdf     rasterized v1 (no text layer -> OCR path, C1)
- sin_encabezados.pdf  headless prose (section-per-page fallback, DP-09)
- protegido.pdf        password-protected (clean rejection path)
- corrupto.pdf         invalid magic bytes (rejection path)
"""

from pathlib import Path

import fitz  # PyMuPDF
from reportlab.lib.pagesizes import letter
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas

OUT_DIR = Path(__file__).resolve().parent / 'pdfs'
PAGE_W, PAGE_H = letter
MARGIN = 72
BODY_FONT = ('Helvetica', 10.5, 14)      # font, size, leading
HEADING_FONT = ('Helvetica-Bold', 14, 20)
FIXED_DATE = 'D:20260101000000Z'

INTRO = (
    'Entre los suscritos, CONSTRUCTORA ANDINA S.A.S., identificada con NIT '
    '900.123.456-7, quien en adelante se denominara EL CONTRATANTE, y '
    'INGENIERIA DEL VALLE LTDA., identificada con NIT 800.987.654-3, quien en '
    'adelante se denominara EL CONTRATISTA, se celebra el presente contrato de '
    'obra civil, que se regira por las siguientes clausulas.'
)

# ---------------------------------------------------------------------------
# Section bodies (deterministic). Keys are logical names; numbering is applied
# per version so renumbering scenarios stay honest.
# ---------------------------------------------------------------------------
BODIES = {
    'objeto': [
        'El presente contrato tiene por objeto la construccion de la segunda '
        'etapa del edificio administrativo del proyecto Torre Central, '
        'incluyendo obra gris, acabados interiores y redes hidrosanitarias, '
        'de acuerdo con los planos y especificaciones tecnicas entregados por '
        'el contratante.',
        'El alcance comprende igualmente el suministro de materiales, mano de '
        'obra, equipos y herramientas necesarios para la correcta ejecucion de '
        'los trabajos descritos.',
    ],
    'definiciones': [
        'Para efectos del presente contrato se entendera por Obra el conjunto '
        'de actividades de construccion descritas en el objeto; por '
        'Interventoria la persona natural o juridica designada por el '
        'contratante para supervisar la ejecucion; y por Acta de Recibo el '
        'documento mediante el cual se formaliza la entrega parcial o total '
        'de la obra.',
        'Los terminos en mayuscula no definidos expresamente tendran el '
        'significado que les asigne la normatividad tecnica colombiana '
        'aplicable.',
    ],
    'obligaciones_contratista_p1': (
        'El contratista se obliga a ejecutar la obra conforme a los planos, '
        'especificaciones y cronograma aprobados, a mantener en el sitio de '
        'trabajo personal calificado y a cumplir la normatividad de seguridad '
        'y salud en el trabajo vigente.'
    ),
    'obligaciones_contratista_p2_v1': (
        'En caso de retraso imputable al contratista, se aplicara una multa '
        'equivalente al dos por ciento (2%) del valor total del contrato por '
        'cada semana de retraso, sin exceder el diez por ciento (10%) del '
        'valor total.'
    ),
    'obligaciones_contratista_p2_v2': (
        'En caso de retraso imputable al contratista, se aplicara una multa '
        'equivalente al cinco por ciento (5%) del valor total del contrato por '
        'cada semana de retraso, sin exceder el veinte por ciento (20%) del '
        'valor total.'
    ),
    'obligaciones_contratante': [
        'El contratante se obliga a entregar oportunamente los disenos, '
        'planos y licencias requeridos, a pagar el valor del contrato en la '
        'forma pactada y a designar la interventoria dentro de los cinco (5) '
        'dias habiles siguientes a la firma.',
        'Asimismo, garantizara el acceso al sitio de la obra y suministrara '
        'los puntos de conexion provisional de agua y energia.',
    ],
    'valor_p1_v1': (
        'El valor total del presente contrato asciende a la suma de cien '
        'millones de pesos colombianos (COP $100.000.000), suma que incluye '
        'todos los impuestos, tasas y contribuciones aplicables.'
    ),
    'valor_p1_v2': (
        'El valor total del presente contrato asciende a la suma de ciento '
        'veinte millones de pesos colombianos (COP $120.000.000), suma que '
        'incluye todos los impuestos, tasas y contribuciones aplicables.'
    ),
    'valor_p2': (
        'El pago se realizara asi: un anticipo del treinta por ciento (30%) a '
        'la firma del acta de inicio, y el saldo mediante actas parciales '
        'mensuales segun avance de obra certificado por la interventoria.'
    ),
    'plazo': [
        'El plazo de ejecucion de la obra sera de ocho (8) meses contados a '
        'partir de la suscripcion del acta de inicio, sin perjuicio de las '
        'suspensiones acordadas por las partes.',
        'Cualquier prorroga debera constar por escrito y ser aprobada por la '
        'interventoria antes del vencimiento del plazo inicial.',
    ],
    'confidencialidad': [
        'Las partes se obligan a mantener bajo estricta reserva la '
        'informacion tecnica, financiera y comercial a la que tengan acceso '
        'con ocasion del presente contrato, obligacion que permanecera '
        'vigente por cinco (5) anos despues de su terminacion.',
        'La informacion solo podra revelarse por orden de autoridad '
        'competente, previa notificacion a la otra parte.',
    ],
    'controversias': [
        'Toda controversia derivada del presente contrato se resolvera en '
        'primera instancia mediante arreglo directo durante treinta (30) '
        'dias; de no lograrse acuerdo, las partes acudiran a un tribunal de '
        'arbitramento ante la Camara de Comercio de Bogota.',
        'El laudo arbitral sera definitivo y vinculante para las partes.',
    ],
    'datos_personales': [
        'Las partes trataran los datos personales recolectados en ejecucion '
        'del contrato conforme a la Ley 1581 de 2012 y sus decretos '
        'reglamentarios, implementando medidas tecnicas y organizativas '
        'adecuadas para su proteccion.',
        'Los titulares podran ejercer sus derechos de conocer, actualizar, '
        'rectificar y suprimir sus datos mediante solicitud escrita dirigida '
        'al responsable del tratamiento.',
    ],
}

V1_SECTIONS = [
    ('1. OBJETO DEL CONTRATO', BODIES['objeto']),
    ('2. DEFINICIONES', BODIES['definiciones']),
    ('3. OBLIGACIONES DEL CONTRATISTA',
     [BODIES['obligaciones_contratista_p1'], BODIES['obligaciones_contratista_p2_v1']]),
    ('4. OBLIGACIONES DEL CONTRATANTE', BODIES['obligaciones_contratante']),
    ('5. VALOR Y FORMA DE PAGO', [BODIES['valor_p1_v1'], BODIES['valor_p2']]),
    ('6. PLAZO DE EJECUCION', BODIES['plazo']),
    ('7. CONFIDENCIALIDAD', BODIES['confidencialidad']),
    ('8. RESOLUCION DE CONTROVERSIAS', BODIES['controversias']),
]

# Truth table (README.md): 3 and 5 modified, 6 removed, 7/8 renumbered with
# identical bodies, new final section added.
V2_SECTIONS = [
    ('1. OBJETO DEL CONTRATO', BODIES['objeto']),
    ('2. DEFINICIONES', BODIES['definiciones']),
    ('3. OBLIGACIONES DEL CONTRATISTA',
     [BODIES['obligaciones_contratista_p1'], BODIES['obligaciones_contratista_p2_v2']]),
    ('4. OBLIGACIONES DEL CONTRATANTE', BODIES['obligaciones_contratante']),
    ('5. VALOR Y FORMA DE PAGO', [BODIES['valor_p1_v2'], BODIES['valor_p2']]),
    ('6. CONFIDENCIALIDAD', BODIES['confidencialidad']),
    ('7. RESOLUCION DE CONTROVERSIAS', BODIES['controversias']),
    ('8. PROTECCION DE DATOS PERSONALES', BODIES['datos_personales']),
]


class Writer:
    """Minimal top-down layout over reportlab's canvas (deterministic)."""

    def __init__(self, path: Path, title: str, encrypt=None):
        self.canvas = canvas.Canvas(
            str(path), pagesize=letter, invariant=1, encrypt=encrypt
        )
        self.canvas.setTitle(title)
        self.canvas.setAuthor('Versiona testdata')
        self.canvas.setSubject('Deterministic test fixture')
        self.y = PAGE_H - MARGIN

    def _ensure_room(self, needed: float):
        if self.y - needed < MARGIN:
            self.canvas.showPage()
            self.y = PAGE_H - MARGIN

    def paragraph(self, text: str, font=BODY_FONT, space_after=8):
        name, size, leading = font
        lines = simpleSplit(text, name, size, PAGE_W - 2 * MARGIN)
        self._ensure_room(len(lines[:3]) * leading)
        self.canvas.setFont(name, size)
        for line in lines:
            self._ensure_room(leading)
            self.canvas.drawString(MARGIN, self.y, line)
            self.y -= leading
        self.y -= space_after

    def heading(self, text: str):
        self._ensure_room(HEADING_FONT[2] + 2 * BODY_FONT[2])
        self.y -= 6
        self.paragraph(text, font=HEADING_FONT, space_after=6)

    def save(self):
        self.canvas.save()


def build_contract(path: Path, title: str, sections):
    writer = Writer(path, title)
    writer.paragraph('CONTRATO DE OBRA CIVIL No. TC-2026-014', font=HEADING_FONT)
    writer.paragraph(INTRO)
    for heading, paragraphs in sections:
        writer.heading(heading)
        for paragraph in paragraphs:
            writer.paragraph(paragraph)
    writer.save()


def build_headless(path: Path):
    writer = Writer(path, 'Memoria descriptiva sin estructura')
    base = (
        'La presente memoria describe de manera continua las actividades '
        'ejecutadas durante el periodo, sin division formal por capitulos, '
        'incluyendo consideraciones tecnicas, administrativas y ambientales '
        'que fueron atendidas por el equipo del proyecto en el frente {n}.'
    )
    for n in range(1, 31):
        writer.paragraph(base.format(n=n))
    writer.save()


def build_protected(path: Path):
    enc = StandardEncryption('versiona-secreta', canPrint=0)
    writer = Writer(path, 'Documento protegido', encrypt=enc)
    writer.paragraph('Este documento esta protegido con contrasena y debe ser '
                     'rechazado por el pipeline de ingesta.')
    writer.save()


def build_corrupt(path: Path):
    path.write_bytes(b'ESTO-NO-ES-UN-PDF\x00\x01\x02 Versiona corrupt fixture\n' * 8)


def build_scanned(src: Path, dst: Path):
    """Rasterize src (150 dpi) into an image-only PDF: the OCR path."""
    with fitz.open(src) as original:
        scanned = fitz.open()
        for page in original:
            pix = page.get_pixmap(dpi=150)
            img_page = scanned.new_page(width=page.rect.width, height=page.rect.height)
            img_page.insert_image(img_page.rect, pixmap=pix)
        scanned.set_metadata({
            'title': 'contrato escaneado v1',
            'author': 'Versiona testdata',
            'creationDate': FIXED_DATE,
            'modDate': FIXED_DATE,
        })
        scanned.save(dst, deflate=True, garbage=4, no_new_id=True)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    build_contract(OUT_DIR / 'contrato_v1.pdf', 'contrato de obra v1', V1_SECTIONS)
    build_contract(OUT_DIR / 'contrato_v2.pdf', 'contrato de obra v2', V2_SECTIONS)
    build_headless(OUT_DIR / 'sin_encabezados.pdf')
    build_protected(OUT_DIR / 'protegido.pdf')
    build_corrupt(OUT_DIR / 'corrupto.pdf')
    build_scanned(OUT_DIR / 'contrato_v1.pdf', OUT_DIR / 'escaneado_v1.pdf')
    for pdf in sorted(OUT_DIR.iterdir()):
        print(f'{pdf.name}: {pdf.stat().st_size} bytes')


if __name__ == '__main__':
    main()
