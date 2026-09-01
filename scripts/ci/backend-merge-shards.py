#!/usr/bin/env python3
"""Combine backend shard coverage data and JUnit reports."""
from __future__ import annotations

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[2] / "backend"
ARTIFACTS = BACKEND / "shard-artifacts"
JUNIT_OUT = BACKEND / "pytest-results.xml"
SUMMED = ("tests", "errors", "failures", "skipped")


def run_coverage(*args: str) -> None:
    command = [sys.executable, "-m", "coverage", *args]
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=BACKEND, check=True)


def coverage_files() -> list[Path]:
    return sorted(
        path
        for path in ARTIFACTS.rglob(".coverage*")
        if path.is_file()
    )


def junit_files() -> list[Path]:
    return sorted(ARTIFACTS.rglob("pytest-results.xml"))


def collect_coverage_data(files: list[Path]) -> None:
    for index, data in enumerate(files):
        shard = data.parent.name
        target = BACKEND / f".coverage.{shard}.{index}"
        target.write_bytes(data.read_bytes())


def merge_junit(files: list[Path]) -> int:
    totals = dict.fromkeys(SUMMED, 0)
    time_total = 0.0
    cases: list[ET.Element] = []

    for path in files:
        header = path.read_bytes()[:4096].lower()
        if b"<!doctype" in header or b"<!entity" in header:
            raise SystemExit(f"ERROR: {path} contains an unexpected XML declaration.")
        for suite in ET.parse(path).iter("testsuite"):
            for key in SUMMED:
                totals[key] += int(suite.get(key) or 0)
            time_total += float(suite.get("time") or 0.0)
            cases.extend(list(suite))

    root = ET.Element("testsuites", name="pytest tests")
    suite = ET.SubElement(root, "testsuite", name="pytest")
    for key in SUMMED:
        suite.set(key, str(totals[key]))
    suite.set("time", f"{time_total:.3f}")
    suite.extend(cases)
    ET.ElementTree(root).write(JUNIT_OUT, encoding="utf-8", xml_declaration=True)

    print(
        f"merged junit: {len(files)} shards -> {totals['tests']} tests, "
        f"{totals['failures']} failures, {totals['errors']} errors, "
        f"{time_total / 60:.1f} min of execution"
    )
    return totals["tests"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expected-shards", type=int, required=True)
    args = parser.parse_args()

    if not ARTIFACTS.is_dir():
        print(f"ERROR: missing {ARTIFACTS}", file=sys.stderr)
        return 2

    data_files = coverage_files()
    reports = junit_files()
    print(f"coverage data files: {len(data_files)}")
    print(f"junit reports:       {len(reports)}")
    if len(data_files) != args.expected_shards:
        print(
            f"ERROR: expected {args.expected_shards} coverage files.",
            file=sys.stderr,
        )
        return 2
    if len(reports) != args.expected_shards:
        print(
            f"ERROR: expected {args.expected_shards} junit reports.",
            file=sys.stderr,
        )
        return 2

    collect_coverage_data(data_files)
    run_coverage("combine", "--rcfile=.coveragerc")
    run_coverage("json", "--rcfile=.coveragerc", "-o", "coverage-backend.json")
    run_coverage("xml", "--rcfile=.coveragerc", "-o", "coverage-backend.xml")

    tests = merge_junit(reports)
    if not tests:
        print("ERROR: the merged junit contains no tests.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
