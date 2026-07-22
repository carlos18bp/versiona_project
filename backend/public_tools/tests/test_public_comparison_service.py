"""Engine reuse for the anonymous comparator (no OCR, no tenancy rows)."""

from pathlib import Path

import pytest

from engine.services.analysis import OcrRequiredError, analyze_bytes
from public_tools.services.public_comparison_service import build_result

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


def fixture_bytes(name: str) -> bytes:
    return (TESTDATA / name).read_bytes()


@pytest.mark.escenario('PC-S01')
def test_analyze_bytes_raises_ocr_required_when_disallowed():
    with pytest.raises(OcrRequiredError):
        analyze_bytes(fixture_bytes('escaneado_v1.pdf'), allow_ocr=False)


@pytest.mark.escenario('PC-S01')
def test_analyze_bytes_default_signature_unchanged_for_native_pdf():
    analysis = analyze_bytes(fixture_bytes('contrato_v1.pdf'))

    assert analysis['scenario'] == 'text_native'
    assert len(analysis['sections']) > 0


@pytest.mark.escenario('PC-S02')
def test_build_result_matches_truth_table_counts():
    result = build_result(
        fixture_bytes('contrato_v1.pdf'), fixture_bytes('contrato_v2.pdf')
    )

    assert result['counts']['modified'] == 2
    assert result['counts']['removed'] == 1
    assert result['counts']['added'] == 1
    assert result['summary_text'] == '2 modificadas, 1 eliminada, 1 agregada'


@pytest.mark.escenario('PC-S02')
def test_build_result_strips_bboxes_and_keeps_word_diff():
    result = build_result(
        fixture_bytes('contrato_v1.pdf'), fixture_bytes('contrato_v2.pdf')
    )

    modified = [s for s in result['sections'] if s['change_type'] == 'modified']
    assert modified[0].get('word_diff')
    assert 'bboxes_from' not in modified[0]
    assert 'bboxes_to' not in modified[0]
