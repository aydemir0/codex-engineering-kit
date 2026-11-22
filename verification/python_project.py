from __future__ import annotations

import ast
import importlib.util
import re
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
    test_families: tuple[tuple[str, str], ...] = ()


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
    status = result.status
    exit_code = result.exit_code
    evidence = _process_evidence(result)
    if name == "tests" and "unittest" in command and status in {"passed", "failed"}:
        # unittest exits 0 even when it discovers *zero* tests.
        output = "\n".join((result.stdout_tail, result.stderr_tail))
        match = re.search(r"\bRan\s+(\d+)\s+tests?\b", output)
        if match and int(match.group(1)) == 0:
            status = "unavailable"
            exit_code = None
            evidence = "unittest discovered zero tests; verification coverage is incomplete."
    return VerificationStep(
        name=name,
        command=list(command),
        status=status,
        exit_code=exit_code,
        duration_ms=result.duration_ms,
        evidence=evidence,
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


def _test_styles(project_path: Path) -> frozenset[str]:
    """Conservatively identify pytest-style functions and unittest.TestCase.

    This is a discovery hint, not proof that a particular test was collected.
    No candidate Python source is imported or executed during inspection.
    """
    styles: set[str] = set()
    tests_dir = project_path / "tests"
    paths = list(tests_dir.rglob("test*.py")) if tests_dir.is_dir() else []
    if tests_dir.is_dir():
        paths += list(tests_dir.rglob("*_test.py"))
    paths += list(project_path.glob("test_*.py"))
    paths += list(project_path.glob("*_test.py"))
    for path in sorted(set(paths)):
        if path.is_symlink() or not path.is_file():
            styles.add("unknown")
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
            styles.add("unknown")
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                styles.add("pytest")
            elif isinstance(node, ast.ClassDef):
                methods = any(
                    isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and method.name.startswith("test_")
                    for method in node.body
                )
                if not methods:
                    continue
                is_unittest = any(
                    (isinstance(base, ast.Name) and base.id == "TestCase")
                    or (isinstance(base, ast.Attribute) and base.attr == "TestCase")
                    for base in node.bases
                )
                if is_unittest:
                    styles.add("unittest")
                elif node.name.startswith("Test"):
                    styles.add("pytest")
    return frozenset(styles)


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

    styles = _test_styles(project_path)
    wants_pytest = _has_pytest_marker(project_path, pyproject) or "pytest" in styles
    has_unittest = "unittest" in styles or (_has_unittest_tree(project_path) and not wants_pytest)
    test_families: list[tuple[str, str]] = []
    if wants_pytest and module_available("pytest"):
        command = [sys.executable, "-m", "pytest"]
        step = _run_step("tests", command, project_path, runner)
        steps.append(step)
        test_families.append(("python-pytest", step.status))
        if "unittest" in styles:
            test_families.append(("python-unittest", "delegated-to-pytest"))
    elif wants_pytest:
        if has_unittest:
            step = _run_step(
                "tests",
                [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
                project_path,
                runner,
            )
            steps.append(step)
            test_families.append(("python-unittest", step.status))
            missing_name = "tests-pytest"
        else:
            missing_name = "tests"
        steps.append(_unavailable(missing_name, [sys.executable, "-m", "pytest"], "pytest"))
        test_families.append(("python-pytest", "unavailable"))
    elif _has_unittest_tree(project_path):
        step = _run_step(
            "tests",
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            project_path,
            runner,
        )
        steps.append(step)
        test_families.append(("python-unittest", step.status))
    else:
        steps.append(_skipped("tests", "No Python test gate discovered."))
        test_families.append(("python", "skipped"))

    if "unknown" in styles:
        steps.append(
            VerificationStep(
                "tests-discovery",
                None,
                "unavailable",
                None,
                0,
                "A candidate test file could not be inspected; test coverage is uncertain.",
            )
        )
        test_families.append(("python-unknown", "unavailable"))

    return PythonPresetResult(steps=tuple(steps), test_families=tuple(test_families))
