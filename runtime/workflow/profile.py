from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

from runtime.state import reject_unsafe_state_path, write_state


KIND = "cek-m2b-workflow-profile"


class WorkflowProfileError(ValueError):
    pass


def _is_within(path: Path, other: Path) -> bool:
    try:
        path.relative_to(other)
        return True
    except ValueError:
        return False


def _disjoint(first: Path, second: Path) -> bool:
    return not _is_within(first, second) and not _is_within(second, first)


def _config_content(root: Path) -> str:
    return (
        'sandbox_mode = "workspace-write"\n'
        '\n[sandbox_workspace_write]\n'
        f"writable_roots = [{json.dumps(str(root))}]\n"
        "network_access = false\n"
    )


def _write_owned_config(path: Path, content: str) -> None:
    reject_unsafe_state_path(path)
    if path.exists():
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            return
        raise WorkflowProfileError("workflow profile config conflicts with the CEK-owned contract")
    descriptor, temporary_name = tempfile.mkstemp(dir=path.parent, prefix=".config.toml.", suffix=".tmp", text=True)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def create_profile(root: Path, normal_codex_home: Path, project: Path, workflow_id: str, cek_sha: str) -> dict[str, str]:
    # Inspect the supplied paths before resolve() can hide a junction or symlink.
    for path in (root, normal_codex_home, project):
        for component in (*reversed(path.absolute().parents), path.absolute()):
            try:
                reject_unsafe_state_path(component)
            except ValueError as exc:
                raise WorkflowProfileError("workflow profile path is unsafe") from exc
    root = root.resolve(strict=False)
    normal = normal_codex_home.resolve(strict=False)
    project = project.resolve(strict=False)
    if not workflow_id or len(cek_sha) != 40:
        raise WorkflowProfileError("workflow profile identity is invalid")
    if not _disjoint(root, normal) or not _disjoint(root, project):
        raise WorkflowProfileError("workflow profile must be disjoint from normal CODEX_HOME and project")
    for ancestor in (root, *root.parents):
        try:
            reject_unsafe_state_path(ancestor)
        except ValueError as exc:
            raise WorkflowProfileError("workflow profile path is unsafe") from exc
    manifest_path = root / ".codex-kit" / "workflow-profile.json"
    reject_unsafe_state_path(manifest_path.parent)
    reject_unsafe_state_path(manifest_path)
    if root.exists() and any(root.iterdir()) and not manifest_path.is_file():
        raise WorkflowProfileError("pre-existing workflow profile is not CEK-owned")
    payload = {
        "workflowId": workflow_id,
        "cekSha": cek_sha,
        "profileRootDigest": hashlib.sha256(str(root).casefold().encode("utf-8")).hexdigest(),
        "allowedStateSubtree": ".codex-kit/workflows",
    }
    if manifest_path.is_file():
        try:
            existing = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise WorkflowProfileError("workflow profile manifest is invalid") from exc
        for key, value in payload.items():
            if existing.get(key) != value:
                raise WorkflowProfileError("workflow profile manifest does not match requested owner")
        _write_owned_config(root / "config.toml", _config_content(root))
        return payload
    write_state(manifest_path, KIND, payload)
    _write_owned_config(root / "config.toml", _config_content(root))
    return payload
