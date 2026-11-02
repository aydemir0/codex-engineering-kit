from __future__ import annotations

import hashlib
import os
import subprocess
from pathlib import Path
from typing import Any, Callable

from runtime.state import reject_unsafe_state_path

from .coordinator import StaleWorkflowError, WorkflowCoordinator, require_m2a_authority
from .ledger import WorkflowLedger
from .model import CandidateIdentity, FailureClass, WorkflowState
from .native import NativeWorkflowError, run_native
from .profile import create_profile


class WorkflowRunError(RuntimeError):
    pass


NativeRunner = Callable[..., subprocess.CompletedProcess[str]]


def workflow_ledger_path(profile_root: Path, workflow_id: str) -> Path:
    if not workflow_id or workflow_id in {".", ".."} or any(character in workflow_id for character in ("/", "\\", ":")):
        raise ValueError("workflow identity is invalid")
    return profile_root / ".codex-kit" / "workflows" / workflow_id / "ledger.json"


def load_ledger(profile_root: Path, workflow_id: str) -> WorkflowLedger:
    for component in (*reversed(profile_root.absolute().parents), profile_root.absolute()):
        reject_unsafe_state_path(component)
    return WorkflowLedger(workflow_ledger_path(profile_root.resolve(strict=True), workflow_id))


def initialize_workflow(
    *,
    profile_root: Path,
    normal_codex_home: Path,
    project: Path,
    workflow_id: str,
    task: str,
    cek_sha: str,
    base_commit_sha: str,
    runtime_identity: dict[str, Any],
    commands: tuple[str, ...],
    scope: tuple[str, ...],
) -> dict[str, Any]:
    if not task.strip() or not commands or not scope:
        raise ValueError("workflow task, command, and scope contracts are required")
    create_profile(profile_root, normal_codex_home, project, workflow_id, cek_sha)
    ledger = WorkflowLedger(workflow_ledger_path(profile_root, workflow_id))
    if ledger.events:
        raise ValueError("workflow already exists; use status or resume")
    coordinator = WorkflowCoordinator.create(
        ledger=ledger,
        workflow_id=workflow_id,
        attempt_id=f"{workflow_id}-attempt-1",
        task_digest=hashlib.sha256(task.encode("utf-8")).hexdigest(),
        base_commit_sha=base_commit_sha,
        cek_sha=cek_sha,
        runtime_identity=runtime_identity,
    )
    coordinator.advance(WorkflowState.CLASSIFIED, {"classification": {
        "taskClass": "ENGINEERING_CHANGE",
        "risk": "BOUNDED",
        "tools": ["codex-native-worktree", "python"],
        "tests": list(commands),
        "review": "reviewer",
    }})
    coordinator.advance(WorkflowState.PLANNED, {"plan": {
        "goal": task,
        "scope": list(scope),
        "redStrategy": "run the frozen focused contract and require the expected behavioral failure",
        "commands": list(commands),
        "reviewer": "project-local reviewer with matching SubagentStart/SubagentStop",
        "security": "no unapproved network, MCP, credential access, or external effect",
        "recovery": "retain every attempt and require ownership-proven cleanup",
    }})
    return workflow_status(profile_root, workflow_id)


def record_transition(
    profile_root: Path,
    workflow_id: str,
    target: WorkflowState,
    evidence: dict[str, Any],
) -> dict[str, Any]:
    ledger = load_ledger(profile_root, workflow_id)
    coordinator = WorkflowCoordinator.load(ledger)
    coordinator.advance(target, evidence)
    return workflow_status(profile_root, workflow_id)


def workflow_status(profile_root: Path, workflow_id: str) -> dict[str, Any]:
    ledger = load_ledger(profile_root, workflow_id)
    coordinator = WorkflowCoordinator.load(ledger)
    public = ledger.sanitized_export()
    return {
        "workflowId": workflow_id,
        "attemptId": coordinator.attempt_id,
        "state": coordinator.state.value,
        "eventCount": len(ledger.events),
        "lastEvent": public["events"][-1],
    }


def explain_workflow(profile_root: Path, workflow_id: str) -> dict[str, Any]:
    status = workflow_status(profile_root, workflow_id)
    last = status["lastEvent"]
    return {
        **status,
        "reasonCode": last.get("reasonCode"),
        "failureClass": last.get("failureClass"),
        "cleanupDisposition": last.get("evidence", {}).get("cleanupDisposition") if isinstance(last.get("evidence"), dict) else None,
    }


def resume_workflow(
    profile_root: Path,
    workflow_id: str,
    candidate: CandidateIdentity,
    worktree_id: str,
) -> dict[str, Any]:
    coordinator = WorkflowCoordinator.load(load_ledger(profile_root, workflow_id))
    coordinator.resume(candidate, worktree_id)
    return workflow_status(profile_root, workflow_id)


def _frozen_prompt(profile_root: Path, workflow_id: str, task: str) -> str:
    return f"""Execute CEK workflow {workflow_id} for this bounded task:
{task}

Use only the frozen plan and scope already recorded by CEK. Work in the native
Codex-managed worktree. Add the missing regression test, record the real
behavioral RED, then make the minimum implementation and record fresh GREEN.
Request exactly one project-local reviewer child. Parent self-review is invalid.
Review acceptance requires matching SubagentStart and SubagentStop identities,
the reviewer role, parent-child correlation, and the exact candidate manifest
and tree. The reviewer child must return one JSON object with disposition,
role=`reviewer`, findings, candidateManifestDigest, and candidateTreeOid.
Give the child the exact manifest digest and tree OID from fresh GREEN and
require those exact values in its result.
Before spawning the reviewer, run `python -B -m scripts.cek_workflow workflow parent --workflow-root {profile_root} --workflow-id {workflow_id}` and use its
hashed parentIdentity when recording REVIEW_RUNNING; then spawn exactly one child.
After the child completes, run `python -B -m scripts.cek_workflow workflow lifecycle --workflow-root {profile_root} --workflow-id {workflow_id}`. It
normalizes the native SubAgentActivity started/completed pair and the child-emitted
structured result into bounded, hashed evidence. Use its output unchanged;
an absent optional hook file is not failure when this native evidence passes.
Record every transition through the existing CEK workflow stage command using
profile {profile_root} and workflow {workflow_id}. Do not fabricate lifecycle,
test, review, or verification evidence. Do not push, merge, tag, release, publish,
deploy, submit, use unapproved MCP/network access, or inspect/copy credentials.
Close only after all six verification dimensions pass and cleanup has an
ownership-proven disposition; otherwise retain the truthful failed or blocked
attempt and return nonzero.
"""


def run_workflow(
    *,
    profile_root: Path,
    normal_codex_home: Path,
    project: Path,
    workflow_id: str,
    task: str,
    cek_sha: str,
    base_commit_sha: str,
    runtime_identity: dict[str, Any],
    commands: tuple[str, ...],
    scope: tuple[str, ...],
    executable: Path,
    authority: object,
    runner: NativeRunner = run_native,
    timeout_seconds: int = 1800,
) -> dict[str, Any]:
    require_m2a_authority(authority)
    initialize_workflow(
        profile_root=profile_root,
        normal_codex_home=normal_codex_home,
        project=project,
        workflow_id=workflow_id,
        task=task,
        cek_sha=cek_sha,
        base_commit_sha=base_commit_sha,
        runtime_identity=runtime_identity,
        commands=commands,
        scope=scope,
    )
    env = dict(os.environ)
    env["CODEX_HOME"] = str(profile_root)
    try:
        completed = runner(
            executable,
            _frozen_prompt(profile_root, workflow_id, task),
            project,
            env,
            timeout_seconds=timeout_seconds,
        )
    except NativeWorkflowError as exc:
        coordinator = WorkflowCoordinator.load(load_ledger(profile_root, workflow_id))
        if coordinator.state not in {WorkflowState.VERIFIED, WorkflowState.FAILED, WorkflowState.BLOCKED,
                                     WorkflowState.ABORTED, WorkflowState.CLEANUP_PENDING, WorkflowState.CLOSED}:
            category = FailureClass.F9_TIMEOUT if exc.diagnostic.code.value == "TIMEOUT" else FailureClass.F4_TOOL_RUNTIME
            coordinator.fail(category, exc.diagnostic.reason_code)
        raise WorkflowRunError(exc.diagnostic.reason_code) from exc
    except subprocess.TimeoutExpired as exc:
        coordinator = WorkflowCoordinator.load(load_ledger(profile_root, workflow_id))
        coordinator.fail(FailureClass.F9_TIMEOUT, "NATIVE_PARENT_TIMEOUT")
        raise WorkflowRunError("NATIVE_PARENT_TIMEOUT") from exc
    coordinator = WorkflowCoordinator.load(load_ledger(profile_root, workflow_id))
    if completed.returncode != 0:
        if coordinator.state not in {WorkflowState.BLOCKED, WorkflowState.FAILED, WorkflowState.ABORTED, WorkflowState.CLOSED}:
            coordinator.fail(FailureClass.F4_TOOL_RUNTIME, "NATIVE_PARENT_FAILED")
        raise WorkflowRunError("NATIVE_PARENT_FAILED")
    if coordinator.state is not WorkflowState.CLOSED:
        if coordinator.state not in {WorkflowState.BLOCKED, WorkflowState.FAILED, WorkflowState.ABORTED}:
            coordinator.fail(FailureClass.F2_IMPLEMENTATION, "WORKFLOW_NOT_CLOSED")
        raise WorkflowRunError("WORKFLOW_NOT_CLOSED")
    return workflow_status(profile_root, workflow_id)
