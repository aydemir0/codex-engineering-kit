from __future__ import annotations

import ast
import importlib.util
import os
import re
import sys
import tempfile
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


def _run_python_tests(command: list[str], project_path: Path) -> ProcessResult:
    # -B alone blocks writing bytecode but still allows reading old caches.
    with tempfile.TemporaryDirectory(prefix="cek-test-bytecode-") as cache:
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=cache)
        return run_command(command, project_path, env=env)


def _incomplete_test_evidence(command: list[str], result: ProcessResult) -> str | None:
    if command[1:3] == ["-m", "unittest"] and result.exit_code in {0, 5}:
        for output in (result.stderr_tail, result.stdout_tail):
            summary = re.search(
                r"(?m)^Ran (\d+) tests? in [^\n]+\n\s*"
                r"(?:OK(?: \(([^()\n]+)\))?|NO TESTS RAN)\s*\Z",
                output,
            )
            if not summary:
                continue
            count = int(summary[1])
            if count == 0:
                return "unittest discovered zero tests; verification coverage is incomplete."
            skipped = re.fullmatch(r"skipped=(\d+)", summary[2] or "")
            if result.status == "passed" and skipped and int(skipped[1]) == count:
                return "unittest skipped all tests; verification coverage is incomplete."
    elif command[1:3] == ["-m", "pytest"] and result.status == "passed":
        output = re.sub(r"\x1b\[[0-9;]*m", "", result.stdout_tail)
        summary = re.search(
            r"(?m)^[= \t]*(\d+ [a-z]+(?:, \d+ [a-z]+)*) in "
            r"\d+(?:\.\d+)?s(?: \([0-9:]+\))?[= \t]*\s*\Z",
            output,
        )
        if not summary or not re.search(r"\b[1-9]\d* passed\b", summary[1]):
            return "pytest did not report a passing test; verification coverage is incomplete."
    return None


def _run_step(name: str, command: list[str], project_path: Path, runner) -> VerificationStep:
    result = runner(command, project_path)
    status = result.status
    exit_code = result.exit_code
    evidence = _process_evidence(result)
    incomplete = _incomplete_test_evidence(command, result)
    if incomplete:
        status = "unavailable"
        exit_code = None
        evidence = incomplete
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


def _test_paths(project_path: Path) -> tuple[Path, ...]:
    tests_dir = project_path / "tests"
    paths = list(project_path.glob("test_*.py")) + list(project_path.glob("*_test.py"))
    if tests_dir.is_dir():
        paths.extend(tests_dir.rglob("test*.py"))
        paths.extend(tests_dir.rglob("*_test.py"))
    return tuple(sorted(set(paths)))


def _test_styles(paths: tuple[Path, ...]) -> frozenset[str]:
    """Conservatively identify pytest-style functions and unittest.TestCase.

    This is a discovery hint, not proof that a particular test was collected.
    No candidate Python source is imported or executed during inspection.
    """
    styles: set[str] = set()
    for path in paths:
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


def _unittest_test_steps(
    project_path: Path,
    paths: tuple[Path, ...],
    runner: Callable[[list[str], Path], ProcessResult],
) -> PythonPresetResult:
    tests_dir = project_path / "tests"
    tree_paths = tuple(path for path in paths if path.is_relative_to(tests_dir))
    tree_discoverable = tuple(
        path for path in tree_paths
        if re.fullmatch(r"test\w*\.py", path.name)
        and all((tests_dir / directory / "__init__.py").is_file()
                for directory in path.relative_to(tests_dir).parents[:-1])
    )
    root_paths = tuple(path for path in paths if path.parent == project_path)
    root_modules = tuple(path.name for path in root_paths if path.stem.isidentifier())
    steps: list[VerificationStep] = []
    families: list[tuple[str, str]] = []
    command = [sys.executable, "-m", "unittest"]
    if tree_discoverable:
        step = _run_step("tests", [*command, "discover", "-s", "tests"], project_path, runner)
        steps.append(step)
        families.append(("python-unittest", step.status))
    if root_modules:
        step = _run_step("tests-root", [*command, *root_modules], project_path, runner)
        steps.append(step)
        families.append(("python-unittest-root", step.status))
    if len(tree_discoverable) != len(tree_paths) or len(root_modules) != len(root_paths):
        steps.append(VerificationStep(
            "tests-layout", None, "unavailable", None, 0,
            "Some candidate tests are outside the supported unittest discovery layout.",
        ))
        families.append(("python-unittest-layout", "unavailable"))
    return PythonPresetResult(tuple(steps), tuple(families))


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
    runner: Callable[[list[str], Path], ProcessResult] | None = None,
) -> PythonPresetResult:
    project_path = Path(project_path)
    pyproject = _read_pyproject(project_path)
    steps: list[VerificationStep] = []
    gate_runner = run_command if runner is None else runner

    if isinstance(pyproject.get("build-system"), dict):
        command = [sys.executable, "-m", "build"]
        if module_available("build"):
            steps.append(_run_step("build", command, project_path, gate_runner))
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
                gate_runner,
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
                gate_runner,
            )
        )
    else:
        steps.append(_skipped("lint", "No runnable Ruff configuration discovered."))

    tests = discover_python_test_steps(project_path, module_available, runner, pyproject=pyproject)
    return PythonPresetResult(steps=tuple(steps) + tests.steps, test_families=tests.test_families)


def discover_python_test_steps(
    project_path: Path,
    module_available: Callable[[str], bool] = _default_module_available,
    runner: Callable[[list[str], Path], ProcessResult] | None = None,
    *,
    pyproject: dict | None = None,
) -> PythonPresetResult:
    if pyproject is None:
        pyproject = _read_pyproject(project_path)
    runner = _run_python_tests if runner is None else runner
    steps: list[VerificationStep] = []
    paths = _test_paths(project_path)
    styles = _test_styles(paths)
    wants_pytest = _has_pytest_marker(project_path, pyproject) or "pytest" in styles
    test_families: list[tuple[str, str]] = []
    if wants_pytest and module_available("pytest"):
        command = [sys.executable, "-m", "pytest"]
        step = _run_step("tests", command, project_path, runner)
        steps.append(step)
        test_families.append(("python-pytest", step.status))
        if "unittest" in styles:
            test_families.append(("python-unittest", "delegated-to-pytest"))
    else:
        if paths and (not wants_pytest or "unittest" in styles):
            unittest_tests = _unittest_test_steps(project_path, paths, runner)
            steps.extend(unittest_tests.steps)
            test_families.extend(unittest_tests.test_families)
        if wants_pytest:
            name = "tests-pytest" if steps else "tests"
            steps.append(_unavailable(name, [sys.executable, "-m", "pytest"], "pytest"))
            test_families.append(("python-pytest", "unavailable"))
        elif not steps:
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
