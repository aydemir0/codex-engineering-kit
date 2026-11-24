from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Sequence

from runtime.state import write_state
from verification.git_checks import run_git_diff_check
from verification.candidate import capture_manifest, manifest_digest, assert_report_current, CandidateIntegrityError
from verification.model import VerificationReport, VerificationStep
from verification.node import discover_node_steps
from verification.python_project import discover_python_steps, discover_python_test_steps
from verification.security import redact_sensitive_text, scan_secret_patterns

SCHEMA_VERSION = 1
REPORT_KIND = "verification-report"
DEFAULT_REPORT_RELATIVE_PATH = Path(".codex-kit") / "verification" / "latest.json"
PYTHON_MARKERS = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "pytest.ini",
    "conftest.py",
)


class VerificationScopeError(ValueError):
    pass


def _has_python_markers(project_path: Path) -> bool:
    if any((project_path / marker).is_file() for marker in PYTHON_MARKERS):
        return True
    tests_dir = project_path / "tests"
    return (
        (
            tests_dir.is_dir()
            and any(
                path.is_file()
                for pattern in ("test*.py", "*_test.py")
                for path in tests_dir.rglob(pattern)
            )
        )
        or any(project_path.glob("test_*.py"))
        or any(project_path.glob("*_test.py"))
    )


def _bounded_evidence(text: str, max_bytes: int = 8192) -> str:
    text = redact_sensitive_text(text)
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _step_payload(step: VerificationStep) -> dict:
    return {
        "name": step.name,
        "command": list(step.command) if step.command is not None else None,
        "status": step.status,
        "exitCode": step.exit_code,
        "durationMs": step.duration_ms,
        "evidence": _bounded_evidence(step.evidence),
    }


def report_record(report: VerificationReport) -> dict:
    if report.status == "passed":
        assert_report_current(Path(report.project_path), report)
    record = {
        "schemaVersion": report.schema_version,
        "kind": REPORT_KIND,
        "projectType": report.project_type,
        "projectPath": report.project_path,
        "packageManager": report.package_manager,
        "steps": [_step_payload(step) for step in report.steps],
        "testFamilies": [
            {"family": family, "status": status}
            for family, status in report.test_families
        ],
        "status": report.status,
        "candidateDigest": report.candidate_digest,
        "candidateManifest": list(report.candidate_manifest),
    }
    if report.project_roots:
        record["projectRoots"] = list(report.project_roots)
    return record


def write_report(path: Path, report: VerificationReport) -> None:
    record = report_record(report)
    payload = {key: value for key, value in record.items() if key not in {"schemaVersion", "kind"}}
    write_state(Path(path), REPORT_KIND, payload)


def _report_status(
    project_type: str,
    project_steps: tuple[VerificationStep, ...],
    steps: tuple[VerificationStep, ...],
    test_families: tuple[tuple[str, str], ...],
) -> str:
    if any(step.status == "failed" for step in steps):
        return "failed"
    if any(step.status == "unavailable" for step in steps):
        return "partial"
    if project_type == "generic":
        return "partial"
    if (
        not test_families
        or not any(status == "passed" for _, status in test_families)
        or any(status in {"skipped", "unavailable", "not-run"} for _, status in test_families)
    ):
        return "partial"
    if not any(step.status == "passed" for step in project_steps):
        return "partial"
    if any(step.status == "passed" for step in steps):
        return "passed"
    return "partial"


def _project_checks(
    project_path: Path,
    explicit_package_manager: str | None,
) -> tuple[str, str | None, tuple[VerificationStep, ...], tuple[tuple[str, str], ...]]:
    package_manager: str | None = None
    test_families: tuple[tuple[str, str], ...] = ()
    if (project_path / "package.json").is_file():
        project_type = "node"
        preset = discover_node_steps(
            project_path,
            explicit_manager=explicit_package_manager,
        )
        package_manager = preset.package_manager
        project_steps = preset.steps
        node_test = next((step for step in project_steps if step.name == "tests"), None)
        test_families = (("node", node_test.status if node_test else "skipped"),)
        if _has_python_markers(project_path):
            python_tests = discover_python_test_steps(project_path)
            project_steps += tuple(
                replace(step, name=f"{step.name}-python") for step in python_tests.steps
            )
            test_families += python_tests.test_families
    elif _has_python_markers(project_path):
        project_type = "python"
        preset = discover_python_steps(project_path)
        project_steps = preset.steps
        test_families = preset.test_families
    else:
        project_type = "generic"
        project_steps = ()
    return project_type, package_manager, project_steps, test_families


def _resolve_project_scopes(project: Path, roots: Sequence[str]) -> tuple[Path, ...]:
    scopes: list[Path] = []
    for name in roots:
        relative = Path(name)
        if relative.anchor or not relative.parts or ".." in relative.parts:
            raise VerificationScopeError("--include-project requires a directory below --project")
        scope = project / relative
        if not scope.is_dir() or scope.resolve() != scope:
            raise VerificationScopeError("--include-project requires an existing directory without path redirects")
        if any(scope.is_relative_to(other) or other.is_relative_to(scope) for other in scopes):
            raise VerificationScopeError("--include-project directories must not overlap or repeat")
        scopes.append(scope)
    return tuple(scopes)


def verify_project(
    project_path: Path | str,
    explicit_package_manager: str | None = None,
    *,
    project_roots: Sequence[str] = (),
) -> VerificationReport:
    project_path = Path(project_path).expanduser().resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path not found: {project_path}")

    scopes = _resolve_project_scopes(project_path, project_roots)
    before = capture_manifest(project_path)
    names: tuple[str, ...] = ()
    if scopes:
        project_type = "multi-root"
        package_manager = None
        project_steps: tuple[VerificationStep, ...] = ()
        test_families: tuple[tuple[str, str], ...] = ()
        for scope in scopes:
            relative = scope.relative_to(project_path)
            bound = tuple(
                (Path(path).relative_to(relative).as_posix(), size, digest, mode)
                for path, size, digest, mode in before if Path(path).is_relative_to(relative)
            )
            if bound != capture_manifest(scope):
                raise VerificationScopeError("Included project files are outside the root candidate manifest")
        for scope in scopes:
            name = scope.relative_to(project_path).as_posix()
            names += (name,)
            _, _, scoped_steps, scoped_families = _project_checks(scope, explicit_package_manager)
            project_steps += tuple(replace(step, name=f"{name}:{step.name}") for step in scoped_steps)
            test_families += tuple(
                (f"{name}:{family}", status)
                for family, status in scoped_families or (("tests", "unavailable"),)
            )
    else:
        project_type, package_manager, project_steps, test_families = _project_checks(
            project_path, explicit_package_manager,
        )

    steps = tuple(project_steps) + (
        scan_secret_patterns(project_path),
        run_git_diff_check(project_path),
    )
    try:
        stable = capture_manifest(project_path) == before
    except (CandidateIntegrityError, OSError):
        stable = False
    steps += (VerificationStep("candidate-integrity", None, "passed" if stable else "failed",
                               0 if stable else 1, 0,
                               "Candidate unchanged" if stable else "Candidate changed during verification; rerun tests"),)
    report = VerificationReport(
        schema_version=SCHEMA_VERSION,
        candidate_digest=manifest_digest(before),
        candidate_manifest=before,
        project_type=project_type,
        project_path=str(project_path),
        package_manager=package_manager,
        steps=steps,
        status=_report_status(project_type, tuple(project_steps), steps, test_families),
        test_families=test_families,
        project_roots=names,
    )
    write_report(project_path / DEFAULT_REPORT_RELATIVE_PATH, report)
    return report
