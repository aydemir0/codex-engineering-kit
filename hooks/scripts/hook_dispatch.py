from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

SUPPORTED_EVENTS = {
    "SessionStart",
    "SessionEnd",
    "PreToolUse",
    "PostToolUse",
    "PreCompact",
    "PostCompact",
    "SubagentStart",
    "SubagentStop",
}

MAX_CONTEXT_CHARS = 6000
STATE_RELATIVE = Path(".codex-kit") / "hooks"
ACCEPTANCE_SENTINEL = "echo cek_hook_deny_fixture"
ACCEPTANCE_SESSION_END_DELAY_MS_ENV = "CEK_HOOK_ACCEPTANCE_SESSION_END_DELAY_MS"
MAX_ACCEPTANCE_SESSION_END_DELAY_MS = 5000
DESTRUCTIVE_COMMANDS = {
    "rm -rf /",
    "rm -rf /*",
    "rm -rf -- /",
    "sudo rm -rf /",
    "sudo rm -rf /*",
    "format c:",
    "remove-item -recurse -force c:\\",
    "del /f /s /q c:\\*",
}


def load_payload(stream: Any) -> dict[str, Any]:
    payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError("hook input must be a JSON object")
    event = payload.get("hook_event_name")
    if event not in SUPPORTED_EVENTS:
        raise ValueError(f"unsupported hook event: {event!r}")
    return payload


def _workspace_dir(payload: dict[str, Any]) -> Path:
    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd.strip():
        raise ValueError("hook input is missing cwd")
    return Path(cwd)


def _state_dir(payload: dict[str, Any]) -> Path:
    state_dir = _workspace_dir(payload) / STATE_RELATIVE
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def _safe_identity(payload: dict[str, Any]) -> dict[str, Any]:
    mapping = {
        "hook_event_name": "event",
        "session_id": "sessionId",
        "turn_id": "turnId",
        "source": "source",
        "trigger": "trigger",
        "tool_name": "toolName",
        "tool_use_id": "toolUseId",
        "agent_id": "agentId",
        "agent_type": "agentType",
    }
    record: dict[str, Any] = {}
    for source, target in mapping.items():
        value = payload.get(source)
        if isinstance(value, (str, bool, int, float)):
            record[target] = value
    return record


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


def _append_event(payload: dict[str, Any], **extra: Any) -> None:
    record = _safe_identity(payload)
    record.update(extra)
    events_path = _state_dir(payload) / "events.jsonl"
    with events_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")


def _normalize_command(payload: dict[str, Any]) -> str:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    if not isinstance(command, str):
        return ""
    return " ".join(command.strip().split()).casefold()


def _is_narrow_destructive_command(payload: dict[str, Any]) -> bool:
    return _normalize_command(payload) in DESTRUCTIVE_COMMANDS


def _is_acceptance_sentinel(payload: dict[str, Any]) -> bool:
    return (
        os.environ.get("CEK_HOOK_ACCEPTANCE") == "1"
        and _normalize_command(payload) == ACCEPTANCE_SENTINEL
    )


def _acceptance_session_end_delay_ms() -> int:
    if os.environ.get("CEK_HOOK_ACCEPTANCE") != "1":
        return 0
    raw_delay = os.environ.get(ACCEPTANCE_SESSION_END_DELAY_MS_ENV)
    if raw_delay is None:
        return 0
    try:
        delay_ms = int(raw_delay)
    except ValueError:
        return 0
    return min(max(delay_ms, 0), MAX_ACCEPTANCE_SESSION_END_DELAY_MS)


def _session_start(payload: dict[str, Any]) -> dict[str, Any]:
    context = "Codex Engineering Kit lifecycle hooks are active for this workspace."
    if payload.get("source") == "compact":
        compact_path = _state_dir(payload) / "compact-state.json"
        if compact_path.is_file():
            try:
                compact_state = json.loads(compact_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                compact_state = None
            if isinstance(compact_state, dict):
                prior_turn = compact_state.get("turnId")
                trigger = compact_state.get("trigger")
                if isinstance(prior_turn, str) and isinstance(trigger, str):
                    context += (
                        f" Resuming after compaction from turn {prior_turn} "
                        f"(trigger {trigger})."
                    )
    context = context[:MAX_CONTEXT_CHARS]
    _append_event(payload)
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context,
        }
    }


def _session_end(payload: dict[str, Any]) -> dict[str, Any]:
    delay_ms = _acceptance_session_end_delay_ms()
    if delay_ms:
        _append_event(
            payload,
            fixture="session-end-timeout",
            phase="started",
            delayMs=delay_ms,
        )
        time.sleep(delay_ms / 1000)

    snapshot = {
        key: value
        for key, value in _safe_identity(payload).items()
        if key in {"event", "sessionId", "turnId"}
    }
    _write_json(_state_dir(payload) / "session-end.json", snapshot)
    _append_event(payload)
    return {}


def _pre_tool_use(payload: dict[str, Any]) -> dict[str, Any]:
    if _is_acceptance_sentinel(payload):
        _append_event(payload, decision="deny", fixture="acceptance")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked by Codex Engineering Kit acceptance fixture."
                ),
            }
        }
    if _is_narrow_destructive_command(payload):
        _append_event(payload, decision="deny")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "Blocked by Codex Engineering Kit: exact destructive root-delete command."
                ),
            }
        }
    _append_event(payload, decision="allow")
    return {}


def _pre_compact(payload: dict[str, Any]) -> dict[str, Any]:
    checkpoint = {
        "sessionId": payload.get("session_id"),
        "turnId": payload.get("turn_id"),
        "trigger": payload.get("trigger"),
    }
    _write_json(_state_dir(payload) / "compact-state.json", checkpoint)
    _append_event(payload)
    return {}


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    event = payload["hook_event_name"]
    if event == "SessionStart":
        return _session_start(payload)
    if event == "SessionEnd":
        return _session_end(payload)
    if event == "PreToolUse":
        return _pre_tool_use(payload)
    if event == "PreCompact":
        return _pre_compact(payload)
    if event in {"PostToolUse", "PostCompact", "SubagentStart", "SubagentStop"}:
        _append_event(payload)
        return {}
    raise ValueError(f"unsupported hook event: {event!r}")


def main() -> int:
    try:
        payload = load_payload(sys.stdin)
        result = dispatch(payload)
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    json.dump(result, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
