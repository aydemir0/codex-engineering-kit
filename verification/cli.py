from __future__ import annotations

import argparse
import json
from pathlib import Path

from verification.runner import report_record, verify_project, write_report

SUPPORTED_MANAGERS = ("npm", "pnpm", "yarn", "bun")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Codex Engineering Kit verification.")
    parser.add_argument("--project", required=True, help="Project directory to verify.")
    parser.add_argument("--package-manager", choices=SUPPORTED_MANAGERS)
    parser.add_argument("--json", action="store_true", dest="json_output")
    parser.add_argument("--output", help="Optional additional verification artifact path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = verify_project(
        Path(args.project),
        explicit_package_manager=args.package_manager,
    )
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

    return 1 if report.status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
