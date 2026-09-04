from __future__ import annotations

from pathlib import Path

from verification.model import VerificationStep
from verification.process import ProcessResult, run_command


def _evidence(result: ProcessResult, default: str) -> str:
    if result.reason:
        return result.reason
    if result.stderr_tail:
        return result.stderr_tail
    if result.stdout_tail:
        return result.stdout_tail
    return default


def run_git_diff_check(project_path: Path) -> VerificationStep:
    project_path = Path(project_path)
    probe = run_command(
        ["git", "rev-parse", "--is-inside-work-tree"],
        project_path,
    )
    if probe.status != "passed" or probe.stdout_tail.strip().casefold() != "true":
        return VerificationStep(
            name="diff",
            command=None,
            status="skipped",
            exit_code=None,
            duration_ms=probe.duration_ms,
            evidence="Not a Git worktree; git diff --check was not run.",
        )

    command = ["git", "diff", "--check"]
    result = run_command(command, project_path)
    return VerificationStep(
        name="diff",
        command=command,
        status=result.status,
        exit_code=result.exit_code,
        duration_ms=result.duration_ms,
        evidence=_evidence(result, "git diff --check passed."),
    )
