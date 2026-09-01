#!/usr/bin/env python3
"""Assign backend test files to duration-balanced CI shards.

Weights come from the pytest JUnit artifact produced by the baseline CI run.
Every discovered file is assigned exactly once. New files use the median
recorded weight, so they cannot silently fall out of the suite.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / "backend"
WEIGHTS = BACKEND / "ci-shard-weights.json"
ROOTS = (
    "accounts/tests",
    "core/tests",
    "orgs/tests",
    "projects/tests",
    "documents/tests",
    "comparisons/tests",
    "reviews/tests",
    "notifications/tests",
    "observations/tests",
    "checks/tests",
    "billing/tests",
    "engine/tests",
    "public_tools/tests",
)
# These files launch real OCR subprocesses. Keeping them on distinct runners,
# together with xdist's loadfile scheduler, avoids saturating one runner with
# concurrent Tesseract processes while preserving duration-based balancing.
DISTINCT_RESOURCE_FILES = (
    "engine/tests/test_analysis_pipeline.py",
    "reviews/tests/test_hardening.py",
)


def discover() -> list[str]:
    """Return every pytest file from the roots declared in pytest.ini."""
    found: set[str] = set()
    for root in ROOTS:
        base = BACKEND / root
        if not base.is_dir():
            continue
        for path in base.rglob("test_*.py"):
            found.add(path.relative_to(BACKEND).as_posix())
    return sorted(found)


def assign(
    files: list[str], count: int, weights: dict[str, float]
) -> list[list[str]]:
    """Longest-processing-time bin packing using measured file durations."""
    default = statistics.median(weights.values()) if weights else 1.0
    bins: list[list[str]] = [[] for _ in range(count)]
    loads = [0.0] * count
    remaining = set(files)
    for index, path in enumerate(DISTINCT_RESOURCE_FILES):
        if path not in remaining:
            continue
        target = index % count
        bins[target].append(path)
        loads[target] += weights.get(path, default)
        remaining.remove(path)
    for path in sorted(
        remaining, key=lambda item: (-weights.get(item, default), item)
    ):
        target = loads.index(min(loads))
        bins[target].append(path)
        loads[target] += weights.get(path, default)
    return [sorted(group) for group in bins]


def parse_shard(raw: str) -> tuple[int, int]:
    try:
        index, count = raw.split("/", 1)
        return int(index), int(count)
    except ValueError as error:
        raise SystemExit(f'ERROR: --shard expects "i/N", received {raw!r}') from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", help='"i/N", one-indexed, matching the CI matrix')
    parser.add_argument("--weights", type=Path, default=WEIGHTS)
    parser.add_argument(
        "--check",
        type=int,
        metavar="N",
        help="verify that N shards cover every discovered file exactly once",
    )
    parser.add_argument(
        "--summary",
        type=int,
        metavar="N",
        help="show the measured load assigned to N shards",
    )
    args = parser.parse_args()

    weights: dict[str, float] = {}
    if args.weights.exists():
        weights = json.loads(args.weights.read_text(encoding="utf-8"))
    elif args.shard:
        print(
            f"WARNING: {args.weights} is missing; using equal weights.",
            file=sys.stderr,
        )

    files = discover()
    if not files:
        print("ERROR: no backend tests were discovered.", file=sys.stderr)
        return 2

    if args.check:
        bins = assign(files, args.check, weights)
        assigned = [path for group in bins for path in group]
        missing = set(files) - set(assigned)
        duplicates = len(assigned) - len(set(assigned))
        print(f"discovered files: {len(files)}")
        print(f"assigned files:   {len(assigned)} across {args.check} shards")
        if missing or duplicates:
            print(
                f"BROKEN: {len(missing)} missing, {duplicates} duplicated",
                file=sys.stderr,
            )
            return 1
        print("OK: every test file belongs to exactly one shard.")
        return 0

    if args.summary:
        bins = assign(files, args.summary, weights)
        default = statistics.median(weights.values()) if weights else 1.0
        total = sum(weights.get(path, default) for path in files)
        mean = total / args.summary
        for index, group in enumerate(bins, 1):
            load = sum(weights.get(path, default) for path in group)
            skew = (load - mean) / mean * 100 if mean else 0.0
            print(
                f"{index}/{args.summary}: {load / 60:.2f} min, "
                f"{len(group)} files, {skew:+.1f}%"
            )
        return 0

    if not args.shard:
        raise SystemExit("ERROR: pass --shard i/N, --check N, or --summary N")

    index, count = parse_shard(args.shard)
    if not 1 <= index <= count:
        raise SystemExit(f"ERROR: shard {index} is outside 1..{count}")
    print(" ".join(assign(files, count, weights)[index - 1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
