from __future__ import annotations

import hashlib
import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from runtime.state import read_state, write_state

from .model import json_safe


KIND = "cek-m2b-workflow-ledger"
SCHEMA_VERSION = 1
ZERO_HASH = "0" * 64
SECRET = re.compile(r"(?i)(authorization\s*:\s*bearer\s+|api[_-]?key\s*[=:]\s*|token\s*[=:]\s*)([^\s,;]+)")
WINDOWS_PATH = re.compile(r"(?i)\b[A-Z]:\\[^\s\"']+")


class LedgerError(ValueError):
    pass


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _event_hash(event: dict[str, Any]) -> str:
    subject = {key: value for key, value in event.items() if key != "eventHash"}
    return hashlib.sha256(_canonical(subject)).hexdigest()


def _sanitize_text(value: str) -> str:
    value = SECRET.sub(lambda match: match.group(1) + "<redacted>", value)
    return WINDOWS_PATH.sub("<private-path>", value)


def _sanitize(value: Any) -> Any:
    if isinstance(value, str):
        return _sanitize_text(value)
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, dict):
        sanitized: dict[str, Any] = {}
        for key, item in value.items():
            folded = key.casefold()
            if folded.endswith("identity") or folded in {"agentid", "agent_id"}:
                sanitized[key] = f"sha256:{hashlib.sha256(str(item).encode('utf-8')).hexdigest()[:20]}" if item else None
            elif folded in {"sessionid", "session_id", "rawoutput", "transcript", "prompt", "auth"}:
                sanitized[key] = "<redacted>"
            else:
                sanitized[key] = _sanitize(item)
        return sanitized
    return value


class WorkflowLedger:
    def __init__(self, path: Path):
        self.path = path
        self.events: list[dict[str, Any]] = []
        payload, error = read_state(path, KIND)
        if error is not None:
            raise LedgerError(f"workflow ledger is unsafe or invalid: {error}")
        if payload is None:
            return
        if payload.get("workflowSchemaVersion") != SCHEMA_VERSION or not isinstance(payload.get("events"), list):
            raise LedgerError("workflow ledger schema is invalid")
        self.events = payload["events"]
        self._validate()

    def _validate(self) -> None:
        previous = ZERO_HASH
        seen: set[str] = set()
        for ordinal, event in enumerate(self.events, 1):
            if not isinstance(event, dict):
                raise LedgerError("workflow ledger event is invalid")
            if event.get("eventOrdinal") != ordinal or event.get("previousEventHash") != previous:
                raise LedgerError("workflow ledger chain is invalid")
            event_id = event.get("eventId")
            if not isinstance(event_id, str) or not event_id or event_id in seen:
                raise LedgerError("workflow ledger event identity is invalid")
            if event.get("eventHash") != _event_hash(event):
                raise LedgerError("workflow ledger event hash is invalid")
            seen.add(event_id)
            previous = event["eventHash"]

    def append(self, event: dict[str, Any]) -> dict[str, Any]:
        if self.path.exists():
            current = WorkflowLedger(self.path)
            if current.events != self.events:
                raise LedgerError("workflow ledger prefix changed on disk")
        normalized = json_safe(event)
        if not isinstance(normalized, dict):
            raise LedgerError("workflow event must be an object")
        row = deepcopy(normalized)
        row["eventOrdinal"] = len(self.events) + 1
        row["previousEventHash"] = self.events[-1]["eventHash"] if self.events else ZERO_HASH
        row["eventHash"] = _event_hash(row)
        updated = [*self.events, row]
        write_state(self.path, KIND, {"workflowSchemaVersion": SCHEMA_VERSION, "events": updated})
        self.events = updated
        return deepcopy(row)

    def append_raw(self, payload: dict[str, Any]) -> dict[str, Any]:
        workflow_id = self.events[-1]["workflowId"] if self.events else "diagnostic"
        attempt_id = self.events[-1]["attemptId"] if self.events else "diagnostic"
        return self.append({
            "workflowId": workflow_id,
            "attemptId": attempt_id,
            "eventId": f"raw-{len(self.events) + 1}",
            "stateFrom": None,
            "stateTo": None,
            "result": "RECORDED",
            "evidence": payload,
        })

    def sanitized_export(self) -> dict[str, Any]:
        return {"schemaVersion": SCHEMA_VERSION, "events": _sanitize(deepcopy(self.events))}
