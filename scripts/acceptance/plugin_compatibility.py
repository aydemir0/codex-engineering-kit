from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

MANIFEST_MODES = {"default", "explicit-hooks"}
REPO_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
SCHEMA_VERSION = 1


@dataclass(frozen=True)
class HookEventSummary:
    session_start: bool
    allow_seen: bool
    post_tool_seen: bool
    deny_fixture_seen: bool
    session_end: bool
    unique_session_count: int
    event_count: int

    def to_record(self) -> dict[str, object]:
        return {
            "sessionStart": self.session_start,
            "allowSeen": self.allow_seen,
            "postToolSeen": self.post_tool_seen,
            "denyFixtureSeen": self.deny_fixture_seen,
            "sessionEnd": self.session_end,
            "uniqueSessionCount": self.unique_session_count,
            "eventCount": self.event_count,
        }


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {".git", ".codex-kit", ".superpowers", "__pycache__"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


def prepare_plugin_copy(repo: Path, destination: Path, manifest_mode: str) -> Path:
    if manifest_mode not in MANIFEST_MODES:
        raise ValueError(f"invalid manifest mode: {manifest_mode!r}")

    repo = repo.resolve()
    destination = destination.resolve()
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")
    if destination == repo or repo in destination.parents:
        raise ValueError("destination must be outside the source repository")

    manifest_path = repo / ".codex-plugin" / "plugin.json"
    hooks_path = repo / "hooks" / "hooks.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing source manifest: {manifest_path}")
    if not hooks_path.is_file():
        raise FileNotFoundError(f"missing source hooks file: {hooks_path}")

    source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(source_manifest, dict):
        raise ValueError("plugin manifest must contain a JSON object")
    if "hooks" in source_manifest:
        raise ValueError("primary plugin manifest unexpectedly contains hooks")

    shutil.copytree(repo, destination, ignore=_copy_ignore)
    copied_manifest_path = destination / ".codex-plugin" / "plugin.json"
    copied_manifest = json.loads(copied_manifest_path.read_text(encoding="utf-8"))
    if not isinstance(copied_manifest, dict):
        raise ValueError("copied plugin manifest must contain a JSON object")

    if manifest_mode == "explicit-hooks":
        copied_manifest["hooks"] = "./hooks/hooks.json"
        copied_manifest_path.write_text(
            json.dumps(copied_manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    elif "hooks" in copied_manifest:
        raise ValueError("default disposable manifest unexpectedly contains hooks")

    return destination


def require_runtime_version(actual: str, expected: str) -> None:
    if actual.strip() != expected.strip():
        raise ValueError(
            f"runtime version mismatch: expected {expected.strip()!r}, got {actual.strip()!r}"
        )


def summarize_hook_events(path: Path) -> HookEventSummary:
    if not path.is_file():
        raise FileNotFoundError(f"missing event file: {path}")

    session_start = False
    allow_seen = False
    post_tool_seen = False
    deny_fixture_seen = False
    session_end = False
    session_ids: set[str] = set()
    event_count = 0

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw_line.strip():
            continue
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSONL at line {line_number}: {exc.msg}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"event line {line_number} must be a JSON object")

        event_count += 1
        session_id = event.get("sessionId")
        if isinstance(session_id, str) and session_id:
            session_ids.add(session_id)

        event_name = event.get("eventName")
        if event_name == "SessionStart":
            session_start = True
        elif event_name == "PreToolUse":
            if event.get("decision") == "allow":
                allow_seen = True
            if event.get("decision") == "deny" and event.get("fixture") == "acceptance":
                deny_fixture_seen = True
        elif event_name == "PostToolUse":
            post_tool_seen = True
        elif event_name == "SessionEnd":
            session_end = True

    return HookEventSummary(
        session_start=session_start,
        allow_seen=allow_seen,
        post_tool_seen=post_tool_seen,
        deny_fixture_seen=deny_fixture_seen,
        session_end=session_end,
        unique_session_count=len(session_ids),
        event_count=event_count,
    )


def _require_complete_summary(summary: HookEventSummary) -> None:
    required = {
        "SessionStart": summary.session_start,
        "PreToolUse allow": summary.allow_seen,
        "PostToolUse": summary.post_tool_seen,
        "acceptance PreToolUse deny": summary.deny_fixture_seen,
        "SessionEnd": summary.session_end,
    }
    missing = [label for label, present in required.items() if not present]
    if missing:
        raise ValueError(f"bounded lifecycle is incomplete: missing {', '.join(missing)}")
    if summary.unique_session_count != 1:
        raise ValueError(
            f"bounded lifecycle requires exactly one session, got {summary.unique_session_count}"
        )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare and summarize Codex Engineering Kit compatibility fixtures."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare = sub.add_parser("prepare")
    prepare.add_argument("--repo", required=True)
    prepare.add_argument("--destination", required=True)
    prepare.add_argument("--manifest-mode", required=True, choices=sorted(MANIFEST_MODES))

    summarize = sub.add_parser("summarize")
    summarize.add_argument("--events", required=True)
    summarize.add_argument("--expected-runtime", required=True)
    summarize.add_argument("--actual-runtime", required=True)
    summarize.add_argument("--manifest-mode", required=True, choices=sorted(MANIFEST_MODES))
    summarize.add_argument("--repo-sha", required=True)
    summarize.add_argument("--output", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "prepare":
            prepared = prepare_plugin_copy(
                Path(args.repo), Path(args.destination), args.manifest_mode
            )
            print(f"PASS: prepared disposable plugin copy at {prepared}")
            return 0

        require_runtime_version(args.actual_runtime, args.expected_runtime)
        if not REPO_SHA_RE.fullmatch(args.repo_sha):
            raise ValueError("repo-sha must be exactly 40 hexadecimal characters")
        summary = summarize_hook_events(Path(args.events))
        _require_complete_summary(summary)
        record: dict[str, object] = {
            "schemaVersion": SCHEMA_VERSION,
            "runtimeVersion": args.actual_runtime.strip(),
            "manifestMode": args.manifest_mode,
            "repositoryCommit": args.repo_sha.lower(),
            "summary": summary.to_record(),
            "result": "PASS",
        }
        _write_json(Path(args.output), record)
        print(f"PASS: bounded compatibility summary written to {Path(args.output)}")
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
