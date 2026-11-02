from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from runtime.state import reject_unsafe_state_path


class NativeLifecycleError(ValueError):
    pass


def _identity_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _matching_sessions(profile_root: Path, workflow_id: str) -> list[list[dict[str, Any]]]:
    if not workflow_id or any(character in workflow_id for character in ("/", "\\", ":")):
        raise NativeLifecycleError("workflow identity is invalid")
    profile = profile_root.resolve(strict=True)
    sessions = profile / "sessions"
    reject_unsafe_state_path(sessions)
    if not sessions.is_dir():
        raise NativeLifecycleError("native session evidence is unavailable")

    matches: list[list[dict[str, Any]]] = []
    for path in sorted(sessions.rglob("*.jsonl")):
        current = path
        while True:
            reject_unsafe_state_path(current)
            if current == sessions:
                break
            current = current.parent
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise NativeLifecycleError("native session evidence is unreadable") from exc
        if workflow_id not in text:
            continue
        lines = text.splitlines()
        if text and not text.endswith(("\n", "\r")):
            lines = lines[:-1]
        records: list[dict[str, Any]] = []
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise NativeLifecycleError("native session evidence is invalid JSONL") from exc
            if isinstance(record, dict):
                records.append(record)
        matches.append(records)
    return matches


def _root_session_ids(records: list[dict[str, Any]]) -> set[str]:
    identities: set[str] = set()
    for record in records:
        if record.get("type") != "session_meta":
            continue
        payload = record.get("payload")
        if not isinstance(payload, dict) or payload.get("source") != "exec" or payload.get("parent_thread_id"):
            continue
        identity = payload.get("id")
        if isinstance(identity, str) and identity:
            identities.add(identity)
    return identities


def _reviewer_result(
    sessions: list[list[dict[str, Any]]], parent: str, child: str
) -> dict[str, Any]:
    matching: list[list[dict[str, Any]]] = []
    for records in sessions:
        for record in records:
            if record.get("type") != "session_meta":
                continue
            payload = record.get("payload")
            if not isinstance(payload, dict) or payload.get("id") != child or payload.get("parent_thread_id") != parent:
                continue
            source = payload.get("source")
            subagent = source.get("subagent") if isinstance(source, dict) else None
            spawn = subagent.get("thread_spawn") if isinstance(subagent, dict) else None
            if (
                not isinstance(spawn, dict)
                or spawn.get("parent_thread_id") != parent
                or spawn.get("agent_path") != "/root/reviewer"
            ):
                raise NativeLifecycleError("native reviewer child provenance is invalid")
            matching.append(records)

    if len(matching) != 1:
        raise NativeLifecycleError("exactly one reviewer child-emitted structured result is required")

    results: list[dict[str, Any]] = []
    for record in matching[0]:
        payload = record.get("payload") if isinstance(record, dict) else None
        if (
            not isinstance(payload, dict)
            or record.get("type") != "response_item"
            or payload.get("type") != "message"
            or payload.get("role") != "assistant"
        ):
            continue
        content = payload.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict) or item.get("type") != "output_text" or not isinstance(item.get("text"), str):
                continue
            try:
                parsed = json.loads(item["text"])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict) and {"disposition", "role", "findings", "candidateManifestDigest", "candidateTreeOid"} <= set(parsed):
                results.append(parsed)

    if len(results) != 1:
        raise NativeLifecycleError("exactly one reviewer child-emitted structured result is required")
    result = results[0]
    if (
        result.get("disposition") not in {"ACCEPT", "REJECT"}
        or result.get("role") != "reviewer"
        or not isinstance(result.get("findings"), list)
        or re.fullmatch(r"[0-9a-f]{64}", str(result.get("candidateManifestDigest"))) is None
        or re.fullmatch(r"[0-9a-f]{40}", str(result.get("candidateTreeOid"))) is None
    ):
        raise NativeLifecycleError("reviewer child-emitted structured result is invalid")
    allowed = ("disposition", "role", "findings", "candidateManifestDigest", "candidateTreeOid", "evidence", "limitation")
    return {key: result[key] for key in allowed if key in result}


def extract_parent_identity(profile_root: Path, workflow_id: str) -> dict[str, str]:
    parents: set[str] = set()
    for records in _matching_sessions(profile_root, workflow_id):
        parents.update(_root_session_ids(records))
    if len(parents) != 1:
        raise NativeLifecycleError("exactly one native parent identity is required")
    return {"source": "codex-native-session", "parentIdentity": _identity_digest(next(iter(parents)))}


def extract_reviewer_lifecycle(profile_root: Path, workflow_id: str) -> dict[str, Any]:
    sessions = _matching_sessions(profile_root, workflow_id)
    pairs: list[tuple[str, str]] = []
    for records in sessions:
        starts: dict[str, list[str]] = {}
        stops: dict[str, list[str]] = {}
        for record in records:
            payload = record.get("payload") if isinstance(record, dict) else None
            item = payload.get("item") if isinstance(payload, dict) else None
            if not isinstance(item, dict) or item.get("type") != "SubAgentActivity":
                continue
            if item.get("agent_path") != "/root/reviewer":
                continue
            parent = payload.get("thread_id")
            child = item.get("agent_thread_id")
            if (
                not isinstance(parent, str)
                or not parent
                or not isinstance(child, str)
                or not child
                or parent == child
            ):
                raise NativeLifecycleError("native reviewer lifecycle identity is invalid")
            target = starts if item.get("kind") == "started" else stops if item.get("kind") == "completed" else None
            if target is not None:
                target.setdefault(child, []).append(parent)
        if not starts and not stops:
            continue
        session_parents = _root_session_ids(records)
        if len(session_parents) != 1:
            raise NativeLifecycleError("native parent identity is invalid")
        session_parent = next(iter(session_parents))
        if any(parent != session_parent for values in (*starts.values(), *stops.values()) for parent in values):
            raise NativeLifecycleError("native reviewer lifecycle identity is invalid")
        for child in sorted(set(starts) | set(stops)):
            if child not in starts or child not in stops:
                continue
            if len(starts[child]) != 1 or len(stops[child]) != 1 or starts[child][0] != stops[child][0]:
                raise NativeLifecycleError("matching reviewer lifecycle is ambiguous")
            pairs.append((starts[child][0], child))

    if not pairs:
        raise NativeLifecycleError("matching reviewer lifecycle was not observed")
    if len(pairs) != 1:
        raise NativeLifecycleError("exactly one reviewer lifecycle is required")
    parent, child = pairs[0]
    child_digest = _identity_digest(child)
    structured_result = _reviewer_result(sessions, parent, child)
    return {
        "source": "codex-native-session",
        "startEvent": "SubagentStart",
        "stopEvent": "SubagentStop",
        "parentIdentity": _identity_digest(parent),
        "startChildIdentity": child_digest,
        "stopChildIdentity": child_digest,
        "childIdentity": child_digest,
        "resultSourceChildIdentity": child_digest,
        "agentType": "reviewer",
        "structuredResult": structured_result,
    }
