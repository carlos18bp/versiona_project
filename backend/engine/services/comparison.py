"""
Comparison engine (docs/plan/05 §4–§5 — flow E1).

Section identity was already resolved at analysis time (steps 1–2 of the
matching: stable_key, then exact body hash for renames), so comparing two
arbitrary versions is a set operation over their SectionVersion snapshots:

  in both  + equal body + equivalent heading  → unchanged
  in both  + equal body + different heading   → renamed_only
  in both  + different body                   → modified   (+ similarity)
  only in `to`                                → added
  only in `from`                              → removed

Word-level diff uses difflib over the normalized text, which is exactly what
the hashes were computed on: what the diff shows is what the invariants see.
"""

import difflib
import re

TOKEN_RE = re.compile(r'\S+|\s+')


def _normalize_heading(heading: str) -> str:
    return ' '.join(heading.lower().split())


def _strip_numbering(heading: str) -> str:
    return re.sub(r'^\s*\d+(\.\d+)*[.)]?\s*', '', _normalize_heading(heading))


def word_diff(text_from: str, text_to: str) -> list[dict]:
    """[{op: equal|delete|insert, text}] over word tokens."""
    words_from = text_from.split()
    words_to = text_to.split()
    matcher = difflib.SequenceMatcher(None, words_from, words_to, autojunk=False)
    ops: list[dict] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            ops.append({'op': 'equal', 'text': ' '.join(words_from[i1:i2])})
        elif tag == 'delete':
            ops.append({'op': 'delete', 'text': ' '.join(words_from[i1:i2])})
        elif tag == 'insert':
            ops.append({'op': 'insert', 'text': ' '.join(words_to[j1:j2])})
        else:  # replace
            ops.append({'op': 'delete', 'text': ' '.join(words_from[i1:i2])})
            ops.append({'op': 'insert', 'text': ' '.join(words_to[j1:j2])})
    return ops


def similarity(text_from: str, text_to: str) -> float:
    return round(
        difflib.SequenceMatcher(None, text_from.split(), text_to.split(), autojunk=False).ratio(),
        4,
    )


def compare_snapshots(snapshots_from: list[dict], snapshots_to: list[dict]) -> dict:
    """Pure comparison over two lists of section snapshots.

    Each snapshot: {stable_key, heading, body_hash, normalized_text, bboxes,
    order_index}. Returns {'diffs': [...], 'counts': {...}, 'summary_text': str}.
    """
    by_key_from = {s['stable_key']: s for s in snapshots_from}
    by_key_to = {s['stable_key']: s for s in snapshots_to}

    diffs: list[dict] = []
    counts = {'unchanged': 0, 'modified': 0, 'added': 0, 'removed': 0, 'renamed_only': 0}

    for key, snap_to in sorted(by_key_to.items(), key=lambda item: item[1]['order_index']):
        snap_from = by_key_from.get(key)
        if snap_from is None:
            change = 'added'
            diffs.append({
                'stable_key': key,
                'heading_from': '',
                'heading_to': snap_to['heading'],
                'change_type': change,
                'similarity': None,
                'order_index': snap_to['order_index'],
                'word_diff': [{'op': 'insert', 'text': snap_to['normalized_text']}],
                'bboxes_from': [],
                'bboxes_to': snap_to['bboxes'],
            })
        elif snap_from['body_hash'] == snap_to['body_hash']:
            headings_match = _strip_numbering(snap_from['heading']) == _strip_numbering(
                snap_to['heading']
            )
            change = 'unchanged' if headings_match else 'renamed_only'
            diffs.append({
                'stable_key': key,
                'heading_from': snap_from['heading'],
                'heading_to': snap_to['heading'],
                'change_type': change,
                'similarity': 1.0,
                'order_index': snap_to['order_index'],
                'word_diff': [],
                'bboxes_from': [],
                'bboxes_to': [],
            })
        else:
            change = 'modified'
            diffs.append({
                'stable_key': key,
                'heading_from': snap_from['heading'],
                'heading_to': snap_to['heading'],
                'change_type': change,
                'similarity': similarity(
                    snap_from['normalized_text'], snap_to['normalized_text']
                ),
                'order_index': snap_to['order_index'],
                'word_diff': word_diff(
                    snap_from['normalized_text'], snap_to['normalized_text']
                ),
                'bboxes_from': snap_from['bboxes'],
                'bboxes_to': snap_to['bboxes'],
            })
        counts[change] += 1

    removed_base = len(by_key_to)
    for offset, (key, snap_from) in enumerate(
        sorted(
            ((k, s) for k, s in by_key_from.items() if k not in by_key_to),
            key=lambda item: item[1]['order_index'],
        )
    ):
        diffs.append({
            'stable_key': key,
            'heading_from': snap_from['heading'],
            'heading_to': '',
            'change_type': 'removed',
            'similarity': None,
            'order_index': removed_base + offset,
            'word_diff': [{'op': 'delete', 'text': snap_from['normalized_text']}],
            'bboxes_from': snap_from['bboxes'],
            'bboxes_to': [],
        })
        counts['removed'] += 1

    return {
        'diffs': diffs,
        'counts': counts,
        'summary_text': summarize(counts),
    }


def summarize(counts: dict) -> str:
    parts = []
    if counts['modified']:
        parts.append(f"{counts['modified']} modificada{'s' if counts['modified'] > 1 else ''}")
    if counts['removed']:
        parts.append(f"{counts['removed']} eliminada{'s' if counts['removed'] > 1 else ''}")
    if counts['added']:
        parts.append(f"{counts['added']} agregada{'s' if counts['added'] > 1 else ''}")
    if counts['renamed_only']:
        parts.append(
            f"{counts['renamed_only']} renumerada{'s' if counts['renamed_only'] > 1 else ''}"
        )
    if not parts:
        return 'Sin cambios entre estas versiones'
    return ', '.join(parts)
