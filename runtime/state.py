from __future__ import annotations

import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1


def reject_unsafe_state_path(path: Path) -> None:
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise ValueError("unsafe state path") from exc
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    file_attributes = getattr(metadata, "st_file_attributes", 0)
    if stat.S_ISLNK(metadata.st_mode) or bool(file_attributes & reparse_flag):
        raise ValueError("unsafe state path")


def _owned_state_ancestors(path: Path) -> list[Path]:
    ancestors = list(reversed((path.parent, *path.parent.parents)))
    for index, ancestor in enumerate(ancestors):
        if ancestor.name.casefold() == ".codex-kit":
            return ancestors[index:]
    return [path.parent]


def _ensure_safe_state_parent(path: Path) -> None:
    ancestors = _owned_state_ancestors(path)
    if len(ancestors) == 1:
        reject_unsafe_state_path(path.parent)
        path.parent.mkdir(parents=True, exist_ok=True)
        reject_unsafe_state_path(path.parent)
        return
    for ancestor in ancestors:
        reject_unsafe_state_path(ancestor)
        ancestor.mkdir(exist_ok=True)
        reject_unsafe_state_path(ancestor)


def write_state(path: Path, kind: str, payload: dict[str, Any]) -> None:
    record: dict[str, Any] = dict(payload)
    record.update({
        "schemaVersion": SCHEMA_VERSION,
        "kind": kind,
    })
    _ensure_safe_state_parent(path)
    reject_unsafe_state_path(path)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
        reject_unsafe_state_path(path)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def read_state(path: Path, expected_kind: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        for ancestor in _owned_state_ancestors(path):
            reject_unsafe_state_path(ancestor)
        reject_unsafe_state_path(path)
    except ValueError:
        return None, "unsafe-path"
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
