#!/usr/bin/env python3
"""
Per-module coverage gate (docs/audit/04 §4): the engine and the D5
invalidation service carry a 95% bar — the global gate is not enough for the
code the crown jewel depends on.

Usage: python3 scripts/ci/coverage-module-gate.py backend/coverage-backend.json
"""

import json
import sys
from pathlib import Path

GATES = {
    'engine/services/analysis.py': 90,
    'engine/services/comparison.py': 95,
    'engine/services/persistence.py': 90,
    # It3 adds: reviews/services/invalidation_service.py -> 95
}


def main() -> int:
    report_path = Path(sys.argv[1] if len(sys.argv) > 1 else 'backend/coverage-backend.json')
    if not report_path.exists():
        print(f'⚠️  coverage report not found: {report_path} (skipping module gate)')
        return 0

    data = json.loads(report_path.read_text())
    files = data.get('files', {})
    failures = []

    print('## Module coverage gate\n')
    print('| Module | Coverage | Gate | Status |')
    print('|---|---|---|---|')
    for module, gate in GATES.items():
        entry = next(
            (value for key, value in files.items() if key.endswith(module)), None
        )
        if entry is None:
            print(f'| `{module}` | — | {gate}% | ⚠️ not measured |')
            continue
        percent = entry['summary']['percent_covered']
        ok = percent >= gate
        print(f'| `{module}` | {percent:.1f}% | {gate}% | {"✅" if ok else "❌"} |')
        if not ok:
            failures.append(f'{module}: {percent:.1f}% < {gate}%')

    if failures:
        print('\n**Gate failed:**')
        for failure in failures:
            print(f'- {failure}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
