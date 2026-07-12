"""Comparison engine vs the fixture truth table (docs/audit/03 E1; testdata/README)."""

from pathlib import Path

import pytest

from engine.services.analysis import analyze_bytes
from engine.services.comparison import compare_snapshots, similarity, summarize, word_diff

TESTDATA = Path(__file__).resolve().parents[3] / 'testdata' / 'pdfs'


def snapshots(fixture: str) -> list[dict]:
    analysis = analyze_bytes((TESTDATA / fixture).read_bytes())
    return [
        {
            'stable_key': section['stable_key'],
            'heading': section['heading'],
            'body_hash': section['body_hash'],
            'normalized_text': section['normalized_text'],
            'bboxes': section['bboxes'],
            'order_index': section['order_index'],
        }
        for section in analysis['sections']
    ]


@pytest.fixture(scope='module')
def v1_v2():
    return compare_snapshots(snapshots('contrato_v1.pdf'), snapshots('contrato_v2.pdf'))


def by_key(result):
    return {diff['stable_key']: diff for diff in result['diffs']}


@pytest.mark.escenario('E1-F01')
def test_truth_table_modified_sections(v1_v2):
    diffs = by_key(v1_v2)

    assert diffs['obligaciones-del-contratista']['change_type'] == 'modified'
    assert diffs['valor-y-forma-de-pago']['change_type'] == 'modified'


@pytest.mark.escenario('E1-F01')
def test_truth_table_removed_section(v1_v2):
    assert by_key(v1_v2)['plazo-de-ejecucion']['change_type'] == 'removed'


@pytest.mark.escenario('E1-F01')
def test_truth_table_added_section(v1_v2):
    assert by_key(v1_v2)['proteccion-de-datos-personales']['change_type'] == 'added'


@pytest.mark.escenario('D5-A01')
def test_truth_table_renumbered_sections_are_not_changes(v1_v2):
    """§7→6 and §8→7 keep their body: identity survives renumbering, and the
    heading difference is pure numbering ⇒ unchanged (never `modified`)."""
    diffs = by_key(v1_v2)

    assert diffs['confidencialidad']['change_type'] == 'unchanged'
    assert diffs['resolucion-de-controversias']['change_type'] == 'unchanged'
    assert diffs['confidencialidad']['heading_from'] != diffs['confidencialidad']['heading_to']


@pytest.mark.escenario('E1-F01')
def test_truth_table_untouched_sections_are_unchanged(v1_v2):
    diffs = by_key(v1_v2)

    for key in ('objeto-del-contrato', 'definiciones', 'obligaciones-del-contratante'):
        assert diffs[key]['change_type'] == 'unchanged', key


@pytest.mark.escenario('E1-F01')
def test_truth_table_exact_counts(v1_v2):
    counts = v1_v2['counts']

    assert counts['modified'] == 2
    assert counts['removed'] == 1
    assert counts['added'] == 1
    assert counts['renamed_only'] == 0


def test_summary_text_is_human_readable(v1_v2):
    assert v1_v2['summary_text'] == '2 modificadas, 1 eliminada, 1 agregada'


@pytest.mark.escenario('E1-L01')
def test_identical_versions_report_no_changes():
    result = compare_snapshots(snapshots('contrato_v1.pdf'), snapshots('contrato_v1.pdf'))

    assert result['counts']['modified'] == 0
    assert result['counts']['added'] == 0
    assert result['counts']['removed'] == 0
    assert result['summary_text'] == 'Sin cambios entre estas versiones'


@pytest.mark.escenario('E1-F01')
def test_modified_section_carries_word_diff_with_the_penalty_change(v1_v2):
    diff = by_key(v1_v2)['obligaciones-del-contratista']

    inserted = ' '.join(op['text'] for op in diff['word_diff'] if op['op'] == 'insert')
    deleted = ' '.join(op['text'] for op in diff['word_diff'] if op['op'] == 'delete')

    # The diff is minimal: only the words that actually changed are marked
    # (the shared "por ciento del valor total" stays `equal`).
    assert 'cinco' in inserted and '(5%)' in inserted
    assert 'dos' in deleted and '(2%)' in deleted
    assert 0.5 < diff['similarity'] < 1.0


@pytest.mark.escenario('E1-F01')
def test_modified_section_carries_bboxes_for_both_sides(v1_v2):
    diff = by_key(v1_v2)['valor-y-forma-de-pago']

    assert diff['bboxes_from'] and diff['bboxes_to']
    for bbox in diff['bboxes_to']:
        assert 0.0 <= bbox['x0'] <= 1.0 and bbox['page'] >= 1


def test_word_diff_of_equal_texts_has_no_insertions():
    ops = word_diff('mismo texto', 'mismo texto')

    assert [op['op'] for op in ops] == ['equal']


def test_similarity_of_identical_text_is_one():
    assert similarity('a b c', 'a b c') == 1.0


def test_summarize_pluralizes_singular_counts():
    text = summarize({'unchanged': 3, 'modified': 1, 'added': 0, 'removed': 1, 'renamed_only': 0})

    assert text == '1 modificada, 1 eliminada'


@pytest.mark.escenario('E1-A01')
def test_comparison_of_non_adjacent_versions_accumulates_changes():
    """v1 ↔ v3 (skipping v2): the §3 change of v2 plus the v3 refinement."""
    result = compare_snapshots(snapshots('contrato_v1.pdf'), snapshots('contrato_v3.pdf'))
    counts = result['counts']

    assert counts['modified'] == 2  # obligaciones + valor
    assert counts['removed'] == 1  # plazo
    assert counts['added'] == 1  # protección de datos
