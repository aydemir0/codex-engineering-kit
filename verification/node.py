from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from verification.model import VerificationStep
from verification.package_manager import detect_package_manager, package_script_command
from verification.process import ProcessResult, run_command

SCRIPT_ALIASES: dict[str, tuple[str, ...]] = {
    "build": ("build",),
    "typecheck": ("typecheck", "type-check", "check-types"),
    "lint": ("lint",),
    "tests": ("test", "tests"),
}


@dataclass(frozen=True)
class NodePresetResult:
    package_manager: str | None
    manager_source: str
    manager_detail: str | None
    steps: tuple[VerificationStep, ...]


def _read_scripts(project_path: Path) -> set[str]:
    package_path = project_path / "package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    scripts = package.get("scripts") if isinstance(package, dict) else None
    if not isinstance(scripts, dict):
        return set()
    return {name for name in scripts if isinstance(name, str)}


def _process_evidence(result: ProcessResult) -> str:
    if result.reason:
        return result.reason
    if result.stderr_tail:
        return result.stderr_tail
    if result.stdout_tail:
        return result.stdout_tail
    return "Command completed without output."


def discover_node_steps(
    project_path: Path,
    explicit_manager: str | None = None,
    which: Callable[[str], str | None] = shutil.which,
    runner=run_command,
) -> NodePresetResult:
    project_path = Path(project_path)
    available_scripts = _read_scripts(project_path)
    manager = detect_package_manager(
        project_path,
        explicit=explicit_manager,
        which=which,
    )

    steps: list[VerificationStep] = []
    for gate, aliases in SCRIPT_ALIASES.items():
        selected_script = next(
            (alias for alias in aliases if alias in available_scripts),
            None,
        )
        if selected_script is None:
            steps.append(
                VerificationStep(
                    name=gate,
                    command=None,
                    status="skipped",
                    exit_code=None,
                    duration_ms=0,
                    evidence=f"No {gate} script discovered.",
                )
            )
            continue

        command = (
            package_script_command(manager.name, selected_script)
            if manager.name is not None
            else None
        )
        if manager.name is None or manager.detail == "unavailable":
            steps.append(
                VerificationStep(
                    name=gate,
                    command=command,
                    status="unavailable",
                    exit_code=None,
                    duration_ms=0,
                    evidence=manager.detail or "No package manager available.",
                )
            )
            continue

        process = runner(command, project_path)
        steps.append(
            VerificationStep(
                name=gate,
                command=list(command),
                status=process.status,
                exit_code=process.exit_code,
                duration_ms=process.duration_ms,
                evidence=_process_evidence(process),
            )
        )

    return NodePresetResult(
        package_manager=manager.name,
        manager_source=manager.source,
        manager_detail=manager.detail,
        steps=tuple(steps),
    )
