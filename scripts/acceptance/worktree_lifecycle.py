from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from runtime.state import write_state

SCHEMA_VERSION = 1
KIND = "worktree-acceptance"
MODE = "manual-git"
COMMAND_TIMEOUT_SECONDS = 20.0


class WorktreeFixtureSafetyError(RuntimeError):
    pass


@dataclass(frozen=True)
class WorktreeAcceptanceResult:
    schema_version: int
    mode: str
    git_version: str | None
    detached_creation: bool
    unique_branches: bool
    isolated_writes: bool
    clean_before_integration: bool
    conflict_stopped: bool
    cleanup_passed: bool
    remaining_fixture_worktrees: int
    blockers: tuple[str, ...]
    status: str


def _git(
    cwd: Path,
    *args: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=COMMAND_TIMEOUT_SECONDS,
        check=False,
        shell=False,
    )
    if check and completed.returncode != 0:
        raise RuntimeError(f"git command failed: {args[0] if args else 'git'}")
    return completed


def _normalized(path: Path) -> str:
    return os.path.normcase(str(path.resolve()))


def _worktree_paths(repo: Path) -> tuple[Path, ...]:
    completed = _git(repo, "worktree", "list", "--porcelain")
    paths: list[Path] = []
    for line in completed.stdout.splitlines():
        if line.startswith("worktree "):
            paths.append(Path(line[9:]).resolve())
    return tuple(paths)


def _listed_worktrees(repo: Path) -> tuple[str, ...]:
    return tuple(_normalized(path) for path in _worktree_paths(repo))


def _fixture_worktree_count(repo: Path, fixture_paths: tuple[Path, ...]) -> int:
    expected = {_normalized(path) for path in fixture_paths}
    return sum(1 for path in _listed_worktrees(repo) if path in expected)


def _remove_fixture_worktree(repo: Path, path: Path, owned: set[Path]) -> None:
    owned_normalized = {_normalized(item) for item in owned}
    if _normalized(path) not in owned_normalized:
        raise WorktreeFixtureSafetyError("refusing to remove an unowned worktree")
    if _normalized(path) not in set(_listed_worktrees(repo)):
        return
    completed = _git(repo, "worktree", "remove", str(path), check=False)
    if completed.returncode != 0:
        raise WorktreeFixtureSafetyError("fixture worktree removal was refused")


def acceptance_record(result: WorktreeAcceptanceResult) -> dict[str, object]:
    return {
        "schemaVersion": result.schema_version,
        "kind": KIND,
        "mode": result.mode,
        "gitVersion": result.git_version,
        "detachedCreation": result.detached_creation,
        "uniqueBranches": result.unique_branches,
        "isolatedWrites": result.isolated_writes,
        "cleanBeforeIntegration": result.clean_before_integration,
        "conflictStopped": result.conflict_stopped,
        "cleanupPassed": result.cleanup_passed,
        "remainingFixtureWorktrees": result.remaining_fixture_worktrees,
        "blockers": list(result.blockers),
        "status": result.status,
    }


def _write_output(path: Path, result: WorktreeAcceptanceResult) -> None:
    record = acceptance_record(result)
    payload = {
        key: value
        for key, value in record.items()
        if key not in {"schemaVersion", "kind"}
    }
    write_state(path, KIND, payload)


def _failure_result(
    *,
    git_version: str | None,
    blocker: str,
    cleanup_passed: bool = False,
    remaining_fixture_worktrees: int = 0,
) -> WorktreeAcceptanceResult:
    return WorktreeAcceptanceResult(
        schema_version=SCHEMA_VERSION,
        mode=MODE,
        git_version=git_version,
        detached_creation=False,
        unique_branches=False,
        isolated_writes=False,
        clean_before_integration=False,
        conflict_stopped=False,
        cleanup_passed=cleanup_passed,
        remaining_fixture_worktrees=remaining_fixture_worktrees,
        blockers=(blocker,),
        status="FAIL",
    )


def run_manual_worktree_acceptance(
    output_path: Path | str,
    *,
    fixture_mode: str = "normal",
) -> WorktreeAcceptanceResult:
    if fixture_mode not in {"normal", "dirty-source"}:
        raise ValueError("unsupported worktree acceptance fixture mode")

    output_path = Path(output_path).expanduser().resolve()
    git_version: str | None = None

    try:
        version = subprocess.run(
            ["git", "--version"],
            text=True,
            capture_output=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        result = _failure_result(git_version=None, blocker="git is unavailable")
        _write_output(output_path, result)
        return result

    if version.returncode != 0:
        result = _failure_result(git_version=None, blocker="git version probe failed")
        _write_output(output_path, result)
        return result
    git_version = version.stdout.strip()

    detached_creation = False
    unique_branches = False
    isolated_writes = False
    clean_before_integration = False
    conflict_stopped = False
    cleanup_passed = False
    remaining_fixture_worktrees = 0
    blockers: list[str] = []

    with tempfile.TemporaryDirectory(prefix="cek-worktree-fixture-") as temp:
        fixture_root = Path(temp)
        repo = fixture_root / "repo"
        worktree_root = fixture_root / "worktrees"
        track_a = worktree_root / "a"
        track_b = worktree_root / "b"
        fixture_paths = (track_a, track_b)
        owned = {track_a, track_b}
        dirty_sentinel = track_a / "dirty-source-sentinel.txt"
        repo.mkdir()
        worktree_root.mkdir()

        try:
            _git(repo, "init")
            _git(repo, "config", "user.name", "CEK Fixture")
            _git(repo, "config", "user.email", "cek-fixture@example.invalid")
            _git(repo, "checkout", "-b", "main")

            (repo / "shared.txt").write_text("base\n", encoding="utf-8")
            _git(repo, "add", "shared.txt")
            _git(repo, "commit", "-m", "fixture base")
            base_sha = _git(repo, "rev-parse", "HEAD").stdout.strip()

            _git(repo, "worktree", "add", "--detach", str(track_a), base_sha)
            _git(repo, "worktree", "add", "--detach", str(track_b), base_sha)

            detached_a = _git(track_a, "symbolic-ref", "-q", "--short", "HEAD", check=False)
            detached_b = _git(track_b, "symbolic-ref", "-q", "--short", "HEAD", check=False)
            detached_creation = detached_a.returncode != 0 and detached_b.returncode != 0

            _git(track_a, "checkout", "-b", "cek-fixture-a")
            _git(track_b, "checkout", "-b", "cek-fixture-b")
            branch_a = _git(track_a, "branch", "--show-current").stdout.strip()
            branch_b = _git(track_b, "branch", "--show-current").stdout.strip()
            unique_branches = (
                branch_a == "cek-fixture-a"
                and branch_b == "cek-fixture-b"
                and branch_a != branch_b
            )

            (track_a / "track-a-only.txt").write_text("track a\n", encoding="utf-8")
            _git(track_a, "add", "track-a-only.txt")
            _git(track_a, "commit", "-m", "track a isolated write")

            (track_b / "track-b-only.txt").write_text("track b\n", encoding="utf-8")
            _git(track_b, "add", "track-b-only.txt")
            _git(track_b, "commit", "-m", "track b isolated write")

            isolated_writes = (
                (track_a / "track-a-only.txt").is_file()
                and not (track_b / "track-a-only.txt").exists()
                and (track_b / "track-b-only.txt").is_file()
                and not (track_a / "track-b-only.txt").exists()
            )

            (track_a / "shared.txt").write_text("alpha\n", encoding="utf-8")
            _git(track_a, "add", "shared.txt")
            _git(track_a, "commit", "-m", "track a conflicting change")

            (track_b / "shared.txt").write_text("beta\n", encoding="utf-8")
            _git(track_b, "add", "shared.txt")
            _git(track_b, "commit", "-m", "track b conflicting change")

            if fixture_mode == "dirty-source":
                dirty_sentinel.write_text("fixture dirty source\n", encoding="utf-8")

            clean_before_integration = (
                _git(track_a, "status", "--porcelain").stdout.strip() == ""
                and _git(track_b, "status", "--porcelain").stdout.strip() == ""
            )

            if not clean_before_integration:
                blockers.append("source worktree is dirty")
            else:
                _git(repo, "merge", "--no-ff", "--no-edit", branch_a)
                merge_b = _git(
                    repo,
                    "merge",
                    "--no-ff",
                    "--no-edit",
                    branch_b,
                    check=False,
                )
                unmerged = _git(
                    repo,
                    "diff",
                    "--name-only",
                    "--diff-filter=U",
                    check=False,
                ).stdout.splitlines()
                conflict_stopped = (
                    merge_b.returncode != 0
                    and "shared.txt" in {item.strip() for item in unmerged}
                )
                if merge_b.returncode != 0:
                    _git(repo, "merge", "--abort", check=False)
                if not conflict_stopped:
                    blockers.append("conflict path did not stop")
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            blockers.append("manual worktree acceptance failed")
        finally:
            if dirty_sentinel.exists():
                dirty_sentinel.unlink()

            for path in fixture_paths:
                try:
                    _remove_fixture_worktree(repo, path, owned)
                except (OSError, RuntimeError, subprocess.TimeoutExpired, WorktreeFixtureSafetyError):
                    pass

            try:
                remaining_fixture_worktrees = _fixture_worktree_count(repo, fixture_paths)
                if remaining_fixture_worktrees == 0:
                    _git(repo, "worktree", "prune", check=False)
                    remaining_fixture_worktrees = _fixture_worktree_count(repo, fixture_paths)
                cleanup_passed = remaining_fixture_worktrees == 0
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                cleanup_passed = False
                remaining_fixture_worktrees = max(remaining_fixture_worktrees, 1)

    if not detached_creation:
        blockers.append("worktrees were not created detached")
    if not unique_branches:
        blockers.append("worktree branches were not unique")
    if not isolated_writes:
        blockers.append("cross-worktree write isolation failed")
    if not cleanup_passed:
        blockers.append("fixture worktree cleanup failed")

    blockers = list(dict.fromkeys(blockers))
    status = "PASS" if not blockers else "FAIL"
    result = WorktreeAcceptanceResult(
        schema_version=SCHEMA_VERSION,
        mode=MODE,
        git_version=git_version,
        detached_creation=detached_creation,
        unique_branches=unique_branches,
        isolated_writes=isolated_writes,
        clean_before_integration=clean_before_integration,
        conflict_stopped=conflict_stopped,
        cleanup_passed=cleanup_passed,
        remaining_fixture_worktrees=remaining_fixture_worktrees,
        blockers=tuple(blockers),
        status=status,
    )
    _write_output(output_path, result)
    return result
