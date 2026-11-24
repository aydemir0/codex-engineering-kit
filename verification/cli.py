from __future__ import annotations

import argparse
import json
from pathlib import Path

from verification.runner import VerificationScopeError, report_record, verify_project, write_report

SUPPORTED_MANAGERS = ("npm", "pnpm", "yarn", "bun")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Codex Engineering Kit verification.")
    parser.add_argument("--project", required=True, help="Project directory to verify.")
    parser.add_argument(
        "--include-project", action="append", default=[], metavar="RELATIVE_DIR",
        help="Verify this project under --project. Repeat to check multiple independent roots.",
    )
    parser.add_argument("--package-manager", choices=SUPPORTED_MANAGERS)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Exit nonzero (2) when test coverage is partial or unsupported.",
    )
    parser.add_argument("--output", help="Optional additional verification artifact path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = verify_project(
            Path(args.project),
            explicit_package_manager=args.package_manager,
            project_roots=args.include_project,
        )
    except VerificationScopeError as exc:
        parser.error(str(exc))
    if args.output:
        write_report(Path(args.output).expanduser(), report)

    record = report_record(report)
    if args.json_output:
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    else:
        print(f"Verification: {report.project_path}")
        for step in report.steps:
            print(f"{step.name.upper():10} {step.status}")
        print(f"STATUS     {report.status}")

    if report.status == "failed":
        return 1
    if report.status == "partial" and args.require_complete:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
