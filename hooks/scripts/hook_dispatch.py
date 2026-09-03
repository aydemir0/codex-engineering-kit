from __future__ import annotations

import json
import sys
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


def load_payload(stream: Any) -> dict[str, Any]:
    payload = json.load(stream)
    if not isinstance(payload, dict):
        raise ValueError("hook input must be a JSON object")
    event = payload.get("hook_event_name")
    if event not in SUPPORTED_EVENTS:
        raise ValueError(f"unsupported hook event: {event!r}")
    return payload


def dispatch(payload: dict[str, Any]) -> dict[str, Any]:
    _ = payload
    return {}


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
