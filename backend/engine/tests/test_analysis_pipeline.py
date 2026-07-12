"""Pure analysis pipeline vs the deterministic fixtures (testdata/README truth
table — docs/audit/03 C1)."""

from pathlib import Path

import pytest

from engine.services.analysis import (
    EncryptedPdfError,
    InvalidPdfError,
    analyze_bytes,
    content_hash,
)

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'

V1_KEYS = [
    'objeto-del-contrato',
    'definiciones',
    'obligaciones-del-contratista',
    'obligaciones-del-contratante',
    'valor-y-forma-de-pago',
    'plazo-de-ejecucion',
    'confidencialidad',
    'resolucion-de-controversias',
]


def load(name: str) -> bytes:
    return (TESTDATA / name).read_bytes()


@pytest.fixture(scope='module')
def analysis_v1():
    return analyze_bytes(load('contrato_v1.pdf'))


@pytest.fixture(scope='module')
def analysis_v2():
    return analyze_bytes(load('contrato_v2.pdf'))


@pytest.mark.escenario('C1-F01')
def test_v1_detects_native_scenario(analysis_v1):
    assert analysis_v1['scenario'] == 'text_native'
    assert analysis_v1['degraded'] is False


@pytest.mark.escenario('C1-F01')
def test_v1_indexes_the_eight_known_sections(analysis_v1):
    keys = [s['stable_key'] for s in analysis_v1['sections'] if s['stable_key'] != '__preamble__']
    non_preamble = [k for k in keys if not k.startswith('contrato-de-obra')]
    assert [k for k in non_preamble if k in V1_KEYS] == V1_KEYS


def test_v1_produces_a_thumbnail(analysis_v1):
    assert analysis_v1['thumbnail_png'][:8] == b'\x89PNG\r\n\x1a\n'


def test_v1_bboxes_are_normalized_top_left(analysis_v1):
    for section in analysis_v1['sections']:
        for bbox in section['bboxes']:
            assert 0.0 <= bbox['x0'] <= bbox['x1'] <= 1.0
            assert 0.0 <= bbox['y0'] <= bbox['y1'] <= 1.0
            assert bbox['page'] >= 1


@pytest.mark.escenario('C2-F01')
def test_truth_table_unchanged_sections_share_body_hash(analysis_v1, analysis_v2):
    """§1, §2, §4 intact; §7/§8 renumbered-only ⇒ same stable_key AND same
    body hash (identity survives renumbering — D5-A01 ground)."""
    v1 = {s['stable_key']: s for s in analysis_v1['sections']}
    v2 = {s['stable_key']: s for s in analysis_v2['sections']}

    for key in ('objeto-del-contrato', 'definiciones', 'obligaciones-del-contratante',
                'confidencialidad', 'resolucion-de-controversias'):
        assert v2[key]['body_hash'] == v1[key]['body_hash'], key


@pytest.mark.escenario('C2-F01')
def test_truth_table_modified_sections_change_body_hash(analysis_v1, analysis_v2):
    v1 = {s['stable_key']: s for s in analysis_v1['sections']}
    v2 = {s['stable_key']: s for s in analysis_v2['sections']}

    for key in ('obligaciones-del-contratista', 'valor-y-forma-de-pago'):
        assert v2[key]['body_hash'] != v1[key]['body_hash'], key


@pytest.mark.escenario('C2-F01')
def test_truth_table_removed_and_added_sections(analysis_v1, analysis_v2):
    v1_keys = {s['stable_key'] for s in analysis_v1['sections']}
    v2_keys = {s['stable_key'] for s in analysis_v2['sections']}

    assert 'plazo-de-ejecucion' in v1_keys - v2_keys
    assert 'proteccion-de-datos-personales' in v2_keys - v1_keys


@pytest.mark.escenario('C1-A03')
def test_headless_pdf_falls_back_to_page_sections():
    result = analyze_bytes(load('sin_encabezados.pdf'))

    assert result['degraded'] is True
    keys = [s['stable_key'] for s in result['sections']]
    assert keys == [f'pagina-{n}' for n in range(1, result['page_count'] + 1)]


@pytest.mark.escenario('C1-A02')
def test_scanned_pdf_goes_through_ocr_with_real_sections():
    """OCR truth table (It5, DP-02): the rasterized contrato_v1 comes back
    with REAL sections extracted from the OCR text layer — exact results."""
    result = analyze_bytes(load('escaneado_v1.pdf'))

    assert result['scenario'] == 'scanned_ocr'
    assert result['degraded'] is False  # confidence well above 0.75
    assert result['ocr_confidence'] > 0.9
    keys = [s['stable_key'] for s in result['sections']]
    assert keys == [
        'preambulo',
        'objeto-del-contrato',
        'obligaciones-del-contratista',
        'obligaciones-del-contratante',
        'valor-y-forma-de-pago',
        'plazo-de-ejecucion',
        'resolucion-de-controversias',
    ]


@pytest.mark.escenario('D5-A03')
def test_low_ocr_confidence_keeps_the_analysis_degraded(monkeypatch):
    """DP-09: below the 0.75 threshold the text exists but hash equality over
    it is a liability — the analysis stays degraded (⇒ D5 coordinator mode)."""
    from engine.services import analysis as analysis_module
    from engine.services.ocr import run_ocr as real_run_ocr

    def low_confidence_ocr(data):
        pdf_with_text, _ = real_run_ocr(data)
        return pdf_with_text, 0.42

    monkeypatch.setattr('engine.services.ocr.run_ocr', low_confidence_ocr)

    result = analysis_module.analyze_bytes(load('escaneado_v1.pdf'))

    assert result['scenario'] == 'scanned_ocr'
    assert result['degraded'] is True
    assert result['ocr_confidence'] == 0.42


@pytest.mark.escenario('C1-E01')
def test_protected_pdf_is_rejected():
    with pytest.raises(EncryptedPdfError):
        analyze_bytes(load('protegido.pdf'))


@pytest.mark.escenario('C1-E02')
def test_corrupt_file_is_rejected():
    with pytest.raises(InvalidPdfError):
        analyze_bytes(load('corrupto.pdf'))


def test_content_hash_is_whitespace_invariant():
    assert content_hash('hola  mundo\n') == content_hash('hola mundo')
