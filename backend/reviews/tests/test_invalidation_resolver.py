"""
D5 resolver — the crown-jewel rule (I7, docs/plan/05 §6).

Two layers: the exact decision table (parametrized) and the PROPERTY TEST that
guards the invariant no example table can prove: for EVERY input, a `preserved`
decision implies verified hash equality of every covered section.
"""

import pytest
from hypothesis import given, settings as hyp_settings
from hypothesis import strategies as st

from reviews.services.invalidation import (
    INVALIDATED,
    MODE_AUTO,
    MODE_COORDINATOR,
    PENDING,
    PRESERVED,
    SealInput,
    resolve_seal_invalidation,
    reviewers_to_notify,
)


def change(change_type: str, hash_from='h1', hash_to='h1', similarity=None) -> dict:
    return {
        'change_type': change_type,
        'body_hash_from': hash_from,
        'body_hash_to': hash_to,
        'similarity': similarity,
    }


def seal(covered: dict, *, seal_id='s1', reviewer='r1', covers_all=False) -> SealInput:
    return SealInput(seal_id=seal_id, reviewer_id=reviewer, covers_all=covers_all,
                     covered=covered)


# ── Decision table (auto mode) ─────────────────────────────────────────────


@pytest.mark.escenario('D5-F02')
def test_seal_over_untouched_sections_is_preserved_with_evidence():
    decisions = resolve_seal_invalidation(
        [seal({'objeto': 'aaa', 'definiciones': 'bbb'})],
        {'objeto': change('unchanged', 'aaa', 'aaa'),
         'definiciones': change('unchanged', 'bbb', 'bbb'),
         'multas': change('modified', 'x', 'y', 0.9)},
    )

    assert decisions[0].decision == PRESERVED
    assert decisions[0].reason_code == 'all_sections_unchanged'
    verified = {v['stable_key'] for v in decisions[0].evidence['verified']}
    assert verified == {'objeto', 'definiciones'}


@pytest.mark.escenario('D5-F01')
def test_seal_over_a_modified_section_is_invalidated():
    decisions = resolve_seal_invalidation(
        [seal({'multas': 'aaa'})],
        {'multas': change('modified', 'aaa', 'zzz', 0.92)},
    )

    assert decisions[0].decision == INVALIDATED
    assert decisions[0].reason_code == 'section_modified'
    assert decisions[0].evidence['changed'][0]['stable_key'] == 'multas'


@pytest.mark.escenario('D5-F03')
def test_seal_over_a_removed_section_is_invalidated():
    decisions = resolve_seal_invalidation(
        [seal({'plazo': 'aaa'})],
        {'plazo': change('removed', 'aaa', None)},
    )

    assert decisions[0].decision == INVALIDATED
    assert decisions[0].reason_code == 'section_removed'


@pytest.mark.escenario('D5-A01')
def test_renamed_only_section_still_invalidates_in_auto_mode():
    """Conservative bias: even a pure renumbering (identical body) does not
    auto-preserve when the heading changed — auto mode invalidates and the
    evidence shows why (a coordinator can overrule)."""
    decisions = resolve_seal_invalidation(
        [seal({'confidencialidad': 'aaa'})],
        {'confidencialidad': change('renamed_only', 'aaa', 'aaa')},
    )

    assert decisions[0].decision == INVALIDATED
    assert decisions[0].reason_code == 'renamed_section'


@pytest.mark.escenario('D5-A02')
def test_unchanged_type_with_hash_mismatch_is_never_preserved():
    """Defense in depth: if a buggy upstream labels a section `unchanged` but
    the hashes differ, the resolver does NOT trust the label."""
    decisions = resolve_seal_invalidation(
        [seal({'objeto': 'sealed-hash'})],
        {'objeto': change('unchanged', 'sealed-hash', 'DIFFERENT')},
    )

    assert decisions[0].decision == INVALIDATED


def test_section_missing_from_comparison_breaks_the_seal():
    decisions = resolve_seal_invalidation(
        [seal({'fantasma': 'aaa'})],
        {'objeto': change('unchanged', 'x', 'x')},
    )

    assert decisions[0].decision == INVALIDATED
    assert decisions[0].evidence['changed'][0]['change_type'] == 'missing'


@pytest.mark.escenario('D5-F04')
def test_covers_all_seal_breaks_on_any_change_including_added():
    decisions = resolve_seal_invalidation(
        [seal({}, covers_all=True)],
        {'objeto': change('unchanged', 'a', 'a'),
         'nueva-clausula': change('added', None, 'n')},
    )

    assert decisions[0].decision == INVALIDATED
    assert decisions[0].reason_code == 'document_changed'


def test_covers_all_seal_survives_a_zero_diff_upload():
    decisions = resolve_seal_invalidation(
        [seal({}, covers_all=True)],
        {'objeto': change('unchanged', 'a', 'a')},
    )

    assert decisions[0].decision == PRESERVED


@pytest.mark.escenario('D5-F01')
def test_partial_evidence_lists_intact_sections_of_a_broken_seal():
    decisions = resolve_seal_invalidation(
        [seal({'multas': 'aaa', 'objeto': 'bbb'})],
        {'multas': change('modified', 'aaa', 'z', 0.8),
         'objeto': change('unchanged', 'bbb', 'bbb')},
    )

    assert decisions[0].decision == INVALIDATED
    intact = {v['stable_key'] for v in decisions[0].evidence['still_intact']}
    assert intact == {'objeto'}


# ── Coordinator mode ───────────────────────────────────────────────────────


@pytest.mark.escenario('D5-A04')
def test_coordinator_mode_leaves_breaking_seals_pending():
    decisions = resolve_seal_invalidation(
        [seal({'multas': 'aaa'})],
        {'multas': change('modified', 'aaa', 'z', 0.9)},
        mode=MODE_COORDINATOR,
    )

    assert decisions[0].decision == PENDING
    assert decisions[0].proposed == INVALIDATED


@pytest.mark.escenario('D5-A04')
def test_coordinator_mode_proposes_preserving_a_pure_rename():
    decisions = resolve_seal_invalidation(
        [seal({'confidencialidad': 'aaa'})],
        {'confidencialidad': change('renamed_only', 'aaa', 'aaa')},
        mode=MODE_COORDINATOR,
    )

    assert decisions[0].decision == PENDING
    assert decisions[0].proposed == PRESERVED


def test_coordinator_mode_still_auto_preserves_proven_equality():
    """Preservation needs no human: it is proven, not judged."""
    decisions = resolve_seal_invalidation(
        [seal({'objeto': 'aaa'})],
        {'objeto': change('unchanged', 'aaa', 'aaa')},
        mode=MODE_COORDINATOR,
    )

    assert decisions[0].decision == PRESERVED


# ── S6: selective notification ─────────────────────────────────────────────


@pytest.mark.escenario('D5-F05')
def test_only_invalidated_reviewers_are_notified():
    decisions = resolve_seal_invalidation(
        [
            seal({'objeto': 'aaa'}, seal_id='sA', reviewer='reviewer-a'),
            seal({'multas': 'bbb'}, seal_id='sB', reviewer='reviewer-b'),
        ],
        {'objeto': change('unchanged', 'aaa', 'aaa'),
         'multas': change('modified', 'bbb', 'z', 0.9)},
    )

    assert reviewers_to_notify(decisions) == ['reviewer-b']


def test_pending_decisions_notify_nobody_yet():
    decisions = resolve_seal_invalidation(
        [seal({'multas': 'aaa'})],
        {'multas': change('modified', 'aaa', 'z', 0.9)},
        mode=MODE_COORDINATOR,
    )

    assert reviewers_to_notify(decisions) == []


# ── THE PROPERTY TEST (I7) ─────────────────────────────────────────────────

CHANGE_TYPES = ['unchanged', 'modified', 'removed', 'renamed_only', 'added',
                'ambiguous', 'split', 'merged']
HASHES = st.sampled_from(['h1', 'h2', 'h3', None])
KEYS = st.sampled_from([f'sec-{i}' for i in range(6)])


@st.composite
def scenario(draw):
    changes = draw(st.dictionaries(
        KEYS,
        st.builds(
            lambda ct, hf, ht, sim: {
                'change_type': ct, 'body_hash_from': hf,
                'body_hash_to': ht, 'similarity': sim,
            },
            st.sampled_from(CHANGE_TYPES), HASHES, HASHES,
            st.one_of(st.none(), st.floats(0, 1)),
        ),
        max_size=6,
    ))
    # seal_id is a UUID primary key in the domain: unique by construction.
    seals = draw(st.lists(
        st.builds(
            lambda sid, cov_all, covered: SealInput(
                seal_id=f's{sid}', reviewer_id=f'r{sid}',
                covers_all=cov_all, covered={} if cov_all else covered,
            ),
            st.integers(0, 4),
            st.booleans(),
            st.dictionaries(KEYS, st.sampled_from(['h1', 'h2', 'h3']), max_size=6),
        ),
        max_size=5,
        unique_by=lambda s: s.seal_id,
    ))
    mode = draw(st.sampled_from([MODE_AUTO, MODE_COORDINATOR]))
    return seals, changes, mode


@hyp_settings(max_examples=300, deadline=None)
@given(scenario())
@pytest.mark.escenario('D5-C01')
@pytest.mark.escenario('D5-E01')
def test_property_preserved_implies_proven_hash_equality(case):
    """I7 — for EVERY input: `preserved` ⇒ every covered section is labeled
    `unchanged` AND its current hash equals the sealed hash; covers_all seals
    are preserved only against a zero-diff comparison. No exceptions."""
    seals, changes, mode = case
    decisions = resolve_seal_invalidation(seals, changes, mode)
    by_id = {s.seal_id: s for s in seals}

    assert len(decisions) == len(seals)
    for decision in decisions:
        source = by_id[decision.seal_id]
        if decision.decision != PRESERVED:
            continue
        if source.covers_all:
            assert all(e['change_type'] == 'unchanged' for e in changes.values())
        else:
            for key, sealed_hash in source.covered.items():
                entry = changes.get(key)
                assert entry is not None
                assert entry['change_type'] == 'unchanged'
                assert entry['body_hash_to'] == sealed_hash


@hyp_settings(max_examples=200, deadline=None)
@given(scenario())
def test_property_auto_mode_never_leaves_a_pending_decision(case):
    seals, changes, _ = case
    decisions = resolve_seal_invalidation(seals, changes, MODE_AUTO)

    assert all(d.decision in (PRESERVED, INVALIDATED) for d in decisions)


@hyp_settings(max_examples=200, deadline=None)
@given(scenario())
def test_property_resolver_is_deterministic(case):
    seals, changes, mode = case

    assert resolve_seal_invalidation(seals, changes, mode) == resolve_seal_invalidation(
        seals, changes, mode
    )
