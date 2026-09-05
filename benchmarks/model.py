from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_CONFIGURATION_PROTOCOL = {
    "A": "naive-always-loaded",
    "B": "progressive-disclosure",
    "C": "isolated-subagent",
}
_CASE_PROTOCOL = {
    "node-small-bug": None,
    "backend-design": "backend-patterns",
    "frontend-review": "frontend-patterns",
    "concurrency-pressure": "concurrency-performance",
    "repository-review": "orchestrator",
}
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


@dataclass(frozen=True)
class BenchmarkConfiguration:
    id: str
    strategy: str
    instruction: str


@dataclass(frozen=True)
class BenchmarkCase:
    id: str
    fixture: str
    repository_commit: str
    prompt: str
    invariants: tuple[str, ...]
    required_skill: str | None


def _json_files(path: Path) -> tuple[Path, ...]:
    if not path.is_dir():
        raise ValueError(f"missing benchmark directory: {path}")
    return tuple(sorted(path.glob("*.json")))


def load_configurations(path: Path) -> tuple[BenchmarkConfiguration, ...]:
    items: list[BenchmarkConfiguration] = []
    seen: set[str] = set()
    for file in _json_files(path):
        record = json.loads(file.read_text(encoding="utf-8"))
        config_id = record.get("id")
        strategy = record.get("strategy")
        instruction = record.get("instruction")
        if config_id in seen:
            raise ValueError(f"duplicate configuration id: {config_id}")
        if config_id not in _CONFIGURATION_PROTOCOL:
            raise ValueError(f"unknown configuration id: {config_id}")
        if strategy != _CONFIGURATION_PROTOCOL[config_id]:
            raise ValueError(f"invalid strategy for configuration {config_id}")
        if not isinstance(instruction, str) or not instruction.strip():
            raise ValueError(f"missing instruction for configuration {config_id}")
        seen.add(config_id)
        items.append(BenchmarkConfiguration(config_id, strategy, instruction.strip()))
    if seen != set(_CONFIGURATION_PROTOCOL):
        raise ValueError("benchmark configurations must contain exactly A, B, and C")
    return tuple(sorted(items, key=lambda item: item.id))


def load_cases(path: Path) -> tuple[BenchmarkCase, ...]:
    items: list[BenchmarkCase] = []
    seen: set[str] = set()
    commit_pins: set[str] = set()
    for file in _json_files(path):
        record = json.loads(file.read_text(encoding="utf-8"))
        case_id = record.get("id")
        fixture = record.get("fixture")
        repository_commit = record.get("repositoryCommit")
        prompt = record.get("prompt")
        invariants = record.get("invariants")
        required_skill = record.get("requiredSkill")

        if case_id in seen:
            raise ValueError(f"duplicate case id: {case_id}")
        if case_id not in _CASE_PROTOCOL:
            raise ValueError(f"unknown benchmark case id: {case_id}")
        if fixture != case_id:
            raise ValueError(f"fixture mismatch for case {case_id}")
        if not isinstance(repository_commit, str) or not _COMMIT_RE.fullmatch(repository_commit):
            raise ValueError(f"malformed repository commit for case {case_id}")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"missing prompt for case {case_id}")
        if (
            not isinstance(invariants, list)
            or len(invariants) < 2
            or not all(isinstance(item, str) and item.strip() for item in invariants)
        ):
            raise ValueError(f"case {case_id} requires at least two invariants")
        if required_skill != _CASE_PROTOCOL[case_id]:
            raise ValueError(f"required skill mismatch for case {case_id}")

        seen.add(case_id)
        commit_pins.add(repository_commit)
        items.append(
            BenchmarkCase(
                id=case_id,
                fixture=fixture,
                repository_commit=repository_commit,
                prompt=prompt.strip(),
                invariants=tuple(item.strip() for item in invariants),
                required_skill=required_skill,
            )
        )
    if seen != set(_CASE_PROTOCOL):
        raise ValueError("benchmark cases must contain the fixed five-case protocol")
    if len(commit_pins) != 1:
        raise ValueError("all benchmark cases must use one fixture commit pin")
    return tuple(sorted(items, key=lambda item: item.id))


def planned_attempt_count(
    cases: tuple[BenchmarkCase, ...],
    configurations: tuple[BenchmarkConfiguration, ...],
    repetitions: int = 3,
) -> int:
    if repetitions < 3:
        raise ValueError("a complete benchmark campaign requires at least three repetitions")
    if {case.id for case in cases} != set(_CASE_PROTOCOL):
        raise ValueError("complete campaign requires the fixed five benchmark cases")
    if {config.id for config in configurations} != set(_CONFIGURATION_PROTOCOL):
        raise ValueError("complete campaign requires configurations A, B, and C")
    return len(cases) * len(configurations) * repetitions
