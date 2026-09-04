from __future__ import annotations

import argparse
import json

from evals.runner import campaign_record, run_offline_campaign


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Codex Engineering Kit eval campaigns.")
    subparsers = parser.add_subparsers(dest="mode", required=True)

    offline = subparsers.add_parser("offline", help="Run deterministic offline fixtures only.")
    offline.add_argument("--cases", required=True, help="Directory containing eval case JSON files.")
    offline.add_argument("--fixtures", required=True, help="Directory containing offline fixture JSON files.")
    offline.add_argument("--json", action="store_true", dest="json_output")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.mode != "offline":
        raise ValueError(f"unsupported eval mode: {args.mode!r}")

    result = run_offline_campaign(args.cases, args.fixtures)
    record = campaign_record(result)

    if args.json_output:
        print(json.dumps(record, sort_keys=True, separators=(",", ":")))
    else:
        print("Eval campaign: offline")
        for case in result.cases:
            print(f"{case.case_id}: {case.result}")
        print(f"STATUS: {result.status}")

    return 1 if result.status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
