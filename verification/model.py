from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VerificationStep:
    name: str
    command: list[str] | None
    status: str
    exit_code: int | None
    duration_ms: int
    evidence: str


@dataclass(frozen=True)
class VerificationReport:
    schema_version: int
    project_type: str
    project_path: str
    package_manager: str | None
    steps: tuple[VerificationStep, ...]
    status: str
