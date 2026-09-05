from __future__ import annotations

from pathlib import Path

from runtime.state import write_state
from verification.git_checks import run_git_diff_check
from verification.model import VerificationReport, VerificationStep
from verification.node import discover_node_steps
from verification.python_project import discover_python_steps
from verification.security import scan_secret_patterns

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


def _has_python_markers(project_path: Path) -> bool:
    if any((project_path / marker).is_file() for marker in PYTHON_MARKERS):
        return True
    tests_dir = project_path / "tests"
    return tests_dir.is_dir() and any(path.is_file() for path in tests_dir.rglob("test*.py"))


def _bounded_evidence(text: str, max_bytes: int = 8192) -> str:
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
    return {
        "schemaVersion": report.schema_version,
        "kind": REPORT_KIND,
        "projectType": report.project_type,
        "projectPath": report.project_path,
        "packageManager": report.package_manager,
        "steps": [_step_payload(step) for step in report.steps],
        "status": report.status,
    }


def write_report(path: Path, report: VerificationReport) -> None:
    record = report_record(report)
    payload = {key: value for key, value in record.items() if key not in {"schemaVersion", "kind"}}
    write_state(Path(path), REPORT_KIND, payload)


def _report_status(project_type: str, project_steps: tuple[VerificationStep, ...], steps: tuple[VerificationStep, ...]) -> str:
    if any(step.status == "failed" for step in steps):
        return "failed"
    if any(step.status == "unavailable" for step in steps):
        return "partial"
    if project_type == "generic":
        return "partial"
    if not any(step.status == "passed" for step in project_steps):
        return "partial"
    if any(step.status == "passed" for step in steps):
        return "passed"
    return "partial"


def verify_project(
    project_path: Path | str,
    explicit_package_manager: str | None = None,
) -> VerificationReport:
    project_path = Path(project_path).expanduser().resolve()
    if not project_path.is_dir():
        raise FileNotFoundError(f"Project path not found: {project_path}")

    package_manager: str | None = None
    if (project_path / "package.json").is_file():
        project_type = "node"
        preset = discover_node_steps(
            project_path,
            explicit_manager=explicit_package_manager,
        )
        package_manager = preset.package_manager
        project_steps = preset.steps
    elif _has_python_markers(project_path):
        project_type = "python"
        preset = discover_python_steps(project_path)
        project_steps = preset.steps
    else:
        project_type = "generic"
        project_steps = ()

    steps = tuple(project_steps) + (
        scan_secret_patterns(project_path),
        run_git_diff_check(project_path),
    )
    report = VerificationReport(
        schema_version=SCHEMA_VERSION,
        project_type=project_type,
        project_path=str(project_path),
        package_manager=package_manager,
        steps=steps,
        status=_report_status(project_type, tuple(project_steps), steps),
    )
    write_report(project_path / DEFAULT_REPORT_RELATIVE_PATH, report)
    return report
