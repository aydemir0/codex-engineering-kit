from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmarks.model import load_cases, load_configurations, planned_attempt_count
from benchmarks.report import build_report, load_run_records, report_record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline Plan E context benchmark protocol/report tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.add_argument("--cases", type=Path, required=True)
    validate.add_argument("--configurations", type=Path, required=True)

    report = subparsers.add_parser("report")
    report.add_argument("--runs", type=Path, required=True)
    report.add_argument("--cases", type=Path, required=True)
    report.add_argument("--configurations", type=Path, required=True)
    report.add_argument("--json", action="store_true", dest="as_json")
    return parser


def _input_fixture(path: Path) -> bool:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return bool(payload.get("fixture")) if isinstance(payload, dict) else False


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    cases = load_cases(args.cases)
    configurations = load_configurations(args.configurations)

    if args.command == "validate":
        attempts = planned_attempt_count(cases, configurations, repetitions=3)
        print(f"PASS: fixed benchmark protocol valid ({attempts} planned attempts)")
        return 0

    runs = load_run_records(args.runs)
    report = build_report(runs, cases, configurations, repetitions=3)
    record = report_record(report)
    record["fixtureInput"] = _input_fixture(args.runs)
    if args.as_json:
        print(json.dumps(record, sort_keys=True))
    else:
        print(
            f"benchmark report: complete={str(report.complete).lower()} "
            f"observed={report.observed_runs}/{report.expected_runs}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
