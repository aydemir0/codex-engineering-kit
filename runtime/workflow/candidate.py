from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from .model import CandidateIdentity


class CandidateError(RuntimeError):
    pass


def _run(repository: Path, args: list[str], *, env: dict[str, str] | None = None, text: bool = True) -> str | bytes:
    completed = subprocess.run(["git", *args], cwd=repository, env=env, capture_output=True, text=text, check=False)
    if completed.returncode != 0:
        stderr = completed.stderr if text else completed.stderr.decode("utf-8", errors="replace")
        raise CandidateError(f"Git candidate snapshot failed: {stderr.strip()}")
    return completed.stdout


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def capture_candidate(repository: Path, worktree_id: str) -> CandidateIdentity:
    repository = repository.resolve(strict=True)
    base = str(_run(repository, ["rev-parse", "HEAD"])).strip()
    base_tree = str(_run(repository, ["rev-parse", "HEAD^{tree}"])).strip()
    branch_result = subprocess.run(["git", "symbolic-ref", "--quiet", "--short", "HEAD"], cwd=repository, capture_output=True, text=True, check=False)
    branch = branch_result.stdout.strip() or None
    index_name = str(_run(repository, ["rev-parse", "--git-path", "index"])).strip()
    index = Path(index_name)
    if not index.is_absolute():
        index = repository / index
    before = hashlib.sha256(index.read_bytes()).hexdigest() if index.is_file() else None

    descriptor, temporary_name = tempfile.mkstemp(prefix="cek-m2b-index-")
    os.close(descriptor)
    temporary = Path(temporary_name)
    temporary.unlink(missing_ok=True)
    env = dict(os.environ)
    env["GIT_INDEX_FILE"] = str(temporary)
    try:
        _run(repository, ["read-tree", "HEAD"], env=env)
        _run(repository, ["add", "-A", "--", "."], env=env)
        tree = str(_run(repository, ["write-tree"], env=env)).strip()
    finally:
        temporary.unlink(missing_ok=True)

    after = hashlib.sha256(index.read_bytes()).hexdigest() if index.is_file() else None
    if before != after:
        raise CandidateError("real Git index changed while computing candidate identity")
    diff = _run(repository, ["diff", "--binary", "--no-ext-diff", base, tree], text=False)
    listing = _run(repository, ["ls-tree", "-r", "-z", tree], text=False)
    assert isinstance(diff, bytes) and isinstance(listing, bytes)
    dirty = tree != base_tree
    commit = None if dirty else base
    diff_digest = _sha256(diff)
    file_set_digest = _sha256(listing)
    manifest = {
        "baseCommitSha": base,
        "candidateCommitSha": commit,
        "candidateTreeOid": tree,
        "candidateDiffDigest": diff_digest,
        "fileSetDigest": file_set_digest,
        "worktreeId": worktree_id,
        "branch": branch,
        "dirty": dirty,
    }
    manifest_digest = _sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8"))
    return CandidateIdentity(base, commit, tree, manifest_digest, diff_digest, file_set_digest, worktree_id, branch, dirty)
