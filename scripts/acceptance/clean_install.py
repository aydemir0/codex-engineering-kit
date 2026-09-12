from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Sequence

from scripts.cek_lifecycle import install, run_codex, uninstall, update, verify, verify_clean


SCHEMA_VERSION = 1
PRIOR_FIXTURE_VERSION = "0.2.0-alpha.0"


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, shell=False, check=False
    )
    if completed.returncode:
        raise RuntimeError(completed.stderr.strip() or "git command failed")
    return completed.stdout.strip()


def _runner(codex: str):
    return lambda command, env: run_codex(codex, command, env)


def _project(root: Path, name: str) -> tuple[Path, bytes]:
    project = root / name
    project.mkdir(parents=True)
    sentinel = project / "user-owned.bin"
    content = b"CEK-WS7-user-owned-sentinel\x00\xff"
    sentinel.write_bytes(content)
    return project, content


def _copy_candidate(repo: Path, target: Path) -> None:
    ignored = shutil.ignore_patterns(".git", ".serena", ".codex-kit", "__pycache__", "*.pyc")
    shutil.copytree(repo, target, ignore=ignored)


def _set_prior_fixture(source: Path) -> None:
    manifest = source / ".codex-plugin" / "plugin.json"
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["version"] = PRIOR_FIXTURE_VERSION
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    reviewer = source / ".codex" / "agents" / "reviewer.toml"
    reviewer.write_bytes(b"# deterministic prior-install fixture\n" + reviewer.read_bytes())


def execute_acceptance(repo: Path, codex: str = "codex") -> dict[str, Any]:
    repo = repo.resolve(strict=True)
    candidate = _git(repo, "rev-parse", "HEAD")
    if _git(repo, "status", "--porcelain", "--untracked-files=no"):
        raise RuntimeError("tracked worktree must be clean before the WS7 acceptance campaign")
    run = _runner(codex)
    checks: dict[str, bool] = {}

    with tempfile.TemporaryDirectory(prefix="cek-ws7-acceptance-") as temporary:
        root = Path(temporary)

        project, sentinel = _project(root, "clean-project")
        home = root / "clean-home"
        home.mkdir()
        home_sentinel = home / "user-owned.bin"
        home_sentinel.write_bytes(sentinel)
        install(repo, project, home, run)
        install_verify = verify(repo, project, home, run)
        checks["cleanInstallVerified"] = install_verify["status"] == "verified"
        checks["reviewerProvisioned"] = (
            project / ".codex" / "agents" / "reviewer.toml"
        ).read_bytes() == (repo / ".codex" / "agents" / "reviewer.toml").read_bytes()
        uninstall(repo, project, home, run)
        clean = verify_clean(repo, project, home, run)
        checks["uninstallVerifiedClean"] = clean["status"] == "clean" and not clean["unownedReviewerPresent"]
        checks["sentinelsPreserved"] = (
            (project / "user-owned.bin").read_bytes() == sentinel
            and home_sentinel.read_bytes() == sentinel
        )
        install(repo, project, home, run)
        checks["reinstallVerified"] = verify(repo, project, home, run)["status"] == "verified"
        uninstall(repo, project, home, run)
        verify_clean(repo, project, home, run)

        conflict_project, conflict_sentinel = _project(root, "conflict-project")
        conflict_home = root / "conflict-home"
        conflict_target = conflict_project / ".codex" / "agents" / "reviewer.toml"
        conflict_target.parent.mkdir(parents=True)
        conflict_target.write_bytes(b"user-owned-reviewer")
        try:
            install(repo, conflict_project, conflict_home, run)
        except Exception as exc:
            checks["reviewerConflictFailedClosed"] = (
                "unowned project-local reviewer" in str(exc)
                and conflict_target.read_bytes() == b"user-owned-reviewer"
                and (conflict_project / "user-owned.bin").read_bytes() == conflict_sentinel
                and not conflict_home.exists()
            )
        else:
            checks["reviewerConflictFailedClosed"] = False

        staged = root / "prior-source"
        _copy_candidate(repo, staged)
        current_manifest = (repo / ".codex-plugin" / "plugin.json").read_bytes()
        current_reviewer = (repo / ".codex" / "agents" / "reviewer.toml").read_bytes()
        _set_prior_fixture(staged)
        update_project, update_sentinel = _project(root, "update-project")
        update_home = root / "update-home"
        install(staged, update_project, update_home, run)
        (staged / ".codex-plugin" / "plugin.json").write_bytes(current_manifest)
        (staged / ".codex" / "agents" / "reviewer.toml").write_bytes(current_reviewer)
        update_result = update(staged, update_project, update_home, run)
        checks["priorToCurrentUpdateVerified"] = (
            update_result["fromVersion"] == PRIOR_FIXTURE_VERSION
            and update_result["toVersion"] == "0.2.0-alpha.1"
            and verify(staged, update_project, update_home, run)["status"] == "verified"
        )
        uninstall(staged, update_project, update_home, run)
        verify_clean(staged, update_project, update_home, run)
        checks["updateSentinelPreserved"] = (
            update_project / "user-owned.bin"
        ).read_bytes() == update_sentinel

    if not all(checks.values()):
        failed = ", ".join(name for name, passed in checks.items() if not passed)
        raise RuntimeError(f"WS7 acceptance checks failed: {failed}")
    return {
        "schemaVersion": SCHEMA_VERSION,
        "kind": "cek-ws7-clean-install-acceptance",
        "result": "PASS",
        "candidateSha": candidate,
        "runtime": "Codex CLI 0.153.0",
        "priorInstallFixtureVersion": PRIOR_FIXTURE_VERSION,
        "checks": checks,
        "sanitized": True,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the disposable CEK WS7 lifecycle campaign.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--codex", default="codex")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = execute_acceptance(Path(args.repo), args.codex)
        output = Path(args.output).resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
