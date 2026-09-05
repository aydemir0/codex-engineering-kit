from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CASE_CLASSES = frozenset({"capability", "regression", "pressure"})
CASE_FIELDS = frozenset({"id", "class", "prompt", "graderType", "expect"})


@dataclass(frozen=True)
class EvalCase:
    id: str
    case_class: str
    prompt: str
    grader_type: str
    expect: dict[str, Any]


@dataclass(frozen=True)
class GradeResult:
    case_id: str
    passed: bool
    grader_type: str
    reasons: tuple[str, ...]


def load_case(path: Path | str) -> EvalCase:
    path = Path(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"eval case must be an object: {path}")
    if set(raw) != CASE_FIELDS:
        raise ValueError(f"eval case fields are invalid: {path}")

    case_id = raw.get("id")
    case_class = raw.get("class")
    prompt = raw.get("prompt")
    grader_type = raw.get("graderType")
    expect = raw.get("expect")

    if not isinstance(case_id, str) or not case_id.strip():
        raise ValueError(f"eval case id must be non-empty: {path}")
    if case_class not in CASE_CLASSES:
        raise ValueError(f"unsupported eval class for {case_id}: {case_class!r}")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"eval case prompt must be non-empty: {case_id}")
    if grader_type != "deterministic":
        raise ValueError(f"unsupported grader type for {case_id}: {grader_type!r}")
    if not isinstance(expect, dict):
        raise ValueError(f"eval expectations must be an object: {case_id}")

    return EvalCase(
        id=case_id,
        case_class=case_class,
        prompt=prompt,
        grader_type=grader_type,
        expect=dict(expect),
    )


def load_cases(case_dir: Path | str) -> tuple[EvalCase, ...]:
    case_dir = Path(case_dir)
    cases = tuple(load_case(path) for path in sorted(case_dir.glob("*.json")))
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate eval case id")
    return tuple(sorted(cases, key=lambda case: case.id))
