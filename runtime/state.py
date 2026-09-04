from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def write_state(path: Path, kind: str, payload: dict[str, Any]) -> None:
    record: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "kind": kind,
    }
    record.update(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def read_state(path: Path, expected_kind: str) -> tuple[dict[str, Any] | None, str | None]:
    if not path.is_file():
        return None, None

    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None, "invalid-json"

    if not isinstance(record, dict):
        return None, "invalid-shape"
    if record.get("schemaVersion") != SCHEMA_VERSION:
        return None, "unsupported-schema"
    if record.get("kind") != expected_kind:
        return None, "kind-mismatch"
    return record, None
