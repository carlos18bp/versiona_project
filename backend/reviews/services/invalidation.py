"""
D5 — SELECTIVE SEAL INVALIDATION: the crown jewel (docs/plan/05 §6).

`resolve_seal_invalidation` is a PURE function: seals + section changes + mode
in, decisions out. No database, no side effects — so the rule that defines the
product can be tested exhaustively (and property-tested).

THE RULE (invariant I7 — conservative bias):
    A seal is PRESERVED only if EVERY section it covers is UNCHANGED, proven
    by body-hash equality. Anything else — modified, removed, renamed,
    ambiguous, a `covers_all` seal facing any change at all — INVALIDATES
    (auto mode) or waits for a coordinator (coordinator mode).
    There is no code path from "not hash-equal" to "preserved".

False-invalidate is acceptable. False-preserve is never (success criterion
S4). And the promise that pays the product (S6): reviewers whose seals were
preserved receive ZERO notifications.
"""

from dataclasses import dataclass, field

PRESERVED = 'preserved'
INVALIDATED = 'invalidated'
PENDING = 'pending_confirmation'

MODE_AUTO = 'auto'
MODE_COORDINATOR = 'coordinator'

# Change types that break a seal (everything except a proven-equal section).
BREAKING = {'modified', 'removed', 'renamed_only', 'ambiguous', 'split', 'merged'}

REASON_UNCHANGED = 'all_sections_unchanged'
REASON_MODIFIED = 'section_modified'
REASON_REMOVED = 'section_removed'
REASON_RENAMED = 'renamed_section'
REASON_AMBIGUOUS = 'ambiguous_match'
REASON_DOCUMENT_CHANGED = 'document_changed'
REASON_UNKNOWN_SECTION = 'section_not_found'


@dataclass(frozen=True)
class SealInput:
    """What the resolver needs to know about one seal."""

    seal_id: str
    reviewer_id: str
    covers_all: bool
    # {stable_key: body_hash_at_sealing_time}
    covered: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    seal_id: str
    reviewer_id: str
    decision: str  # preserved | invalidated | pending_confirmation
    proposed: str  # what auto mode would have decided (for the coordinator UI)
    reason_code: str
    evidence: dict


def resolve_seal_invalidation(
    seals: list[SealInput],
    changes: dict,
    mode: str = MODE_AUTO,
) -> list[Decision]:
    """
    changes: {stable_key: {'change_type': str, 'body_hash_from': str|None,
              'body_hash_to': str|None}} for EVERY section of the comparison.
    """
    decisions: list[Decision] = []
    document_touched = any(
        entry['change_type'] in BREAKING or entry['change_type'] == 'added'
        for entry in changes.values()
    )

    for seal in seals:
        if seal.covers_all:
            # A whole-document seal covers the whole: a new section alters the
            # whole, so even `added` breaks it (docs/plan/05 §6d row 5).
            if document_touched:
                decisions.append(
                    _breaking(seal, REASON_DOCUMENT_CHANGED, mode, {
                        'changed': [
                            {'stable_key': key, 'change_type': entry['change_type']}
                            for key, entry in sorted(changes.items())
                            if entry['change_type'] != 'unchanged'
                        ],
                    })
                )
            else:
                decisions.append(_preserved(seal, {
                    'method': 'covers_all_zero_diffs',
                    'verified': [],
                }))
            continue

        verified = []
        breakers = []
        for key, sealed_hash in sorted(seal.covered.items()):
            entry = changes.get(key)
            if entry is None:
                # The section vanished from the comparison entirely: we cannot
                # prove equality ⇒ it breaks (conservative bias).
                breakers.append({'stable_key': key, 'change_type': 'missing'})
                continue
            change_type = entry['change_type']
            hash_to = entry.get('body_hash_to')
            # The ONLY path to preservation: proven hash equality.
            if change_type == 'unchanged' and hash_to is not None and hash_to == sealed_hash:
                verified.append({
                    'stable_key': key,
                    'hash_from': sealed_hash,
                    'hash_to': hash_to,
                })
            else:
                breakers.append({
                    'stable_key': key,
                    'change_type': change_type,
                    'similarity': entry.get('similarity'),
                })

        if not breakers:
            decisions.append(_preserved(seal, {
                'method': 'body_hash_equal',
                'verified': verified,
            }))
            continue

        reason = _reason_for(breakers)
        decisions.append(
            _breaking(seal, reason, mode, {
                'changed': breakers,
                # Partial certificate: the covered sections that DID stay
                # intact are still recorded (docs/plan/05 §6d).
                'still_intact': verified,
            })
        )

    return decisions


def _reason_for(breakers: list[dict]) -> str:
    types = {breaker.get('change_type') for breaker in breakers}
    if 'removed' in types or 'missing' in types:
        return REASON_REMOVED
    if types & {'ambiguous', 'split', 'merged'}:
        return REASON_AMBIGUOUS
    if 'modified' in types:
        return REASON_MODIFIED
    if 'renamed_only' in types:
        return REASON_RENAMED
    return REASON_UNKNOWN_SECTION


def _preserved(seal: SealInput, evidence: dict) -> Decision:
    return Decision(
        seal_id=seal.seal_id,
        reviewer_id=seal.reviewer_id,
        decision=PRESERVED,
        proposed=PRESERVED,
        reason_code=REASON_UNCHANGED,
        evidence=evidence,
    )


def _breaking(seal: SealInput, reason: str, mode: str, evidence: dict) -> Decision:
    """Auto mode decides now; coordinator mode proposes and waits.

    Note the asymmetry that protects S4: in coordinator mode a renamed-only
    section is PROPOSED as preserved (the body is provably identical, only the
    heading moved), while anything with a different body is proposed as
    invalidated. Either way a human confirms — and either way, nothing is
    preserved automatically without hash equality.
    """
    proposed = PRESERVED if reason == REASON_RENAMED else INVALIDATED
    if mode == MODE_COORDINATOR:
        return Decision(
            seal_id=seal.seal_id,
            reviewer_id=seal.reviewer_id,
            decision=PENDING,
            proposed=proposed,
            reason_code=reason,
            evidence=evidence,
        )
    return Decision(
        seal_id=seal.seal_id,
        reviewer_id=seal.reviewer_id,
        decision=INVALIDATED,
        proposed=INVALIDATED,
        reason_code=reason,
        evidence=evidence,
    )


def reviewers_to_notify(decisions: list[Decision]) -> list[str]:
    """S6: ONLY reviewers whose seals were invalidated. Preserved reviewers get
    nothing — that silence IS the product promise."""
    return sorted({
        decision.reviewer_id
        for decision in decisions
        if decision.decision == INVALIDATED
    })
