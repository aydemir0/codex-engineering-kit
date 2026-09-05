from __future__ import annotations

import importlib.util
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from verification.model import VerificationStep
from verification.process import ProcessResult, run_command


@dataclass(frozen=True)
class PythonPresetResult:
    steps: tuple[VerificationStep, ...]


def _default_module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, AttributeError, ValueError):
        return False


def _read_pyproject(project_path: Path) -> dict:
    path = project_path / "pyproject.toml"
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            data = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _process_evidence(result: ProcessResult) -> str:
    if result.reason:
        return result.reason
    if result.stderr_tail:
        return result.stderr_tail
    if result.stdout_tail:
        return result.stdout_tail
    return "Command completed without output."


def _run_step(name: str, command: list[str], project_path: Path, runner) -> VerificationStep:
    result = runner(command, project_path)
    return VerificationStep(
        name=name,
        command=list(command),
        status=result.status,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        evidence=_process_evidence(result),
    )


def _skipped(name: str, evidence: str) -> VerificationStep:
    return VerificationStep(
        name=name,
        command=None,
        status="skipped",
        exit_code=None,
        duration_ms=0,
        evidence=evidence,
    )


def _unavailable(name: str, command: list[str], module: str) -> VerificationStep:
    return VerificationStep(
        name=name,
        command=list(command),
        status="unavailable",
        exit_code=None,
        duration_ms=0,
        evidence=f"Python module '{module}' is unavailable.",
    )


def _has_pytest_marker(project_path: Path, pyproject: dict) -> bool:
    if (project_path / "pytest.ini").is_file() or (project_path / "conftest.py").is_file():
        return True
    tool = pyproject.get("tool")
    return (
        isinstance(tool, dict)
        and isinstance(tool.get("pytest"), dict)
        and isinstance(tool["pytest"].get("ini_options"), dict)
    )


def _has_unittest_tree(project_path: Path) -> bool:
    tests_dir = project_path / "tests"
    if not tests_dir.is_dir():
        return False
    return any(path.is_file() for path in tests_dir.rglob("test*.py"))


def _ruff_configured(project_path: Path, pyproject: dict) -> bool:
    tool = pyproject.get("tool")
    if isinstance(tool, dict) and isinstance(tool.get("ruff"), dict):
        return True
    return any((project_path / name).is_file() for name in ("ruff.toml", ".ruff.toml"))


def _mypy_configured(project_path: Path, pyproject: dict) -> bool:
    tool = pyproject.get("tool")
    if isinstance(tool, dict) and isinstance(tool.get("mypy"), dict):
        return True
    return any((project_path / name).is_file() for name in ("mypy.ini", ".mypy.ini"))


def discover_python_steps(
    project_path: Path,
    module_available: Callable[[str], bool] = _default_module_available,
    runner=run_command,
) -> PythonPresetResult:
    project_path = Path(project_path)
    pyproject = _read_pyproject(project_path)
    steps: list[VerificationStep] = []

    if isinstance(pyproject.get("build-system"), dict):
        command = [sys.executable, "-m", "build"]
        if module_available("build"):
            steps.append(_run_step("build", command, project_path, runner))
        else:
            steps.append(_unavailable("build", command, "build"))
    else:
        steps.append(_skipped("build", "No Python build-system configuration discovered."))

    if _mypy_configured(project_path, pyproject) and module_available("mypy"):
        steps.append(
            _run_step(
                "typecheck",
                [sys.executable, "-m", "mypy", "."],
                project_path,
                runner,
            )
        )
    else:
        steps.append(
            _skipped(
                "typecheck",
                "No runnable mypy configuration discovered.",
            )
        )

    if _ruff_configured(project_path, pyproject) and module_available("ruff"):
        steps.append(
            _run_step(
                "lint",
                [sys.executable, "-m", "ruff", "check", "."],
                project_path,
                runner,
            )
        )
    else:
        steps.append(_skipped("lint", "No runnable Ruff configuration discovered."))

    if _has_pytest_marker(project_path, pyproject):
        command = [sys.executable, "-m", "pytest"]
        if module_available("pytest"):
            steps.append(_run_step("tests", command, project_path, runner))
        else:
            steps.append(_unavailable("tests", command, "pytest"))
    elif _has_unittest_tree(project_path):
        steps.append(
            _run_step(
                "tests",
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                project_path,
                runner,
            )
        )
    else:
        steps.append(_skipped("tests", "No Python test gate discovered."))

    return PythonPresetResult(steps=tuple(steps))
