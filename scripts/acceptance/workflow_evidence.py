from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterator, Sequence

SCHEMA_VERSION = 1
FIXTURE_NAME = "representative-workflow-v1"

REQUIRED_STAGES = (
    "classify",
    "plan",
    "red",
    "implement",
    "green",
    "review",
    "verify",
)

SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")

SENSITIVE_PATTERNS = (
    re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE),
    re.compile(r"/Users/"),
    re.compile(r"/home/"),
    re.compile(r"\bsessionId\b"),
    re.compile(r"\bghp_[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


def _iter_strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
        return

    if isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                yield key
            yield from _iter_strings(item)
        return

    if isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)


def _contains_sensitive_content(record: dict[str, object]) -> bool:
    for value in _iter_strings(record):
        if any(pattern.search(value) for pattern in SENSITIVE_PATTERNS):
            return True
    return False


def validate_workflow_record(
    record: dict[str, object],
) -> tuple[str, ...]:
    errors: list[str] = []

    if record.get("schemaVersion") != SCHEMA_VERSION:
        errors.append("schemaVersion must be 1")

    repository_commit = record.get("repositoryCommit")
    if (
        not isinstance(repository_commit, str)
        or SHA_RE.fullmatch(repository_commit) is None
    ):
        errors.append(
            "repositoryCommit must be exactly 40 hexadecimal characters"
        )

    runtime_version = record.get("runtimeVersion")
    if (
        not isinstance(runtime_version, str)
        or not runtime_version.strip()
    ):
        errors.append("runtimeVersion must be a non-empty exact string")

    if record.get("fixture") != FIXTURE_NAME:
        errors.append(
            "fixture must be representative-workflow-v1"
        )

    stages = record.get("stages")

    if not isinstance(stages, list):
        errors.append("stages must be a list")
    else:
        names: list[str] = []

        for index, stage in enumerate(stages):
            if not isinstance(stage, dict):
                errors.append(
                    f"stage {index} must be an object"
                )
                continue

            name = stage.get("name")
            if not isinstance(name, str):
                errors.append(
                    f"stage {index} must have a string name"
                )
                continue

            names.append(name)

            if stage.get("result") != "PASS":
                errors.append(
                    f"stage {name} must have result PASS"
                )

            evidence = stage.get("evidence")
            if (
                not isinstance(evidence, list)
                or not evidence
                or not all(
                    isinstance(item, str) and item.strip()
                    for item in evidence
                )
            ):
                errors.append(
                    f"PASS stage {name} must contain evidence"
                )

        if len(names) != len(set(names)):
            errors.append("stage names must not be duplicated")

        if tuple(names) != REQUIRED_STAGES:
            errors.append(
                "stages must appear exactly once in required workflow order"
            )

    if record.get("result") != "PASS":
        errors.append("result must be PASS")

    if _contains_sensitive_content(record):
        errors.append(
            "record contains machine-local or sensitive content"
        )

    return tuple(errors)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate a sanitized CEK representative workflow "
            "evidence record."
        )
    )

    sub = parser.add_subparsers(
        dest="command",
        required=True,
    )

    validate = sub.add_parser("validate")
    validate.add_argument(
        "--record",
        required=True,
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.command != "validate":
        return 1

    try:
        payload = json.loads(
            Path(args.record).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        print(
            "FAIL: workflow evidence record could not be read",
            file=sys.stderr,
        )
        return 1

    if not isinstance(payload, dict):
        print(
            "FAIL: workflow evidence record must be a JSON object",
            file=sys.stderr,
        )
        return 1

    errors = validate_workflow_record(payload)

    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1

    print("PASS: representative workflow evidence validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
