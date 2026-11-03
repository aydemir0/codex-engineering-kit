"""Local workflow evidence CLI. Does not create authentication or execution authority."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any
from runtime.state import reject_unsafe_state_path

class LifecycleError(ValueError):
    pass

def _load_json(path: Path, label: str) -> dict[str, Any]:
    for item in (*reversed(path.absolute().parents), path.absolute()):
        reject_unsafe_state_path(item)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LifecycleError(label + " must be a JSON object")
    return payload

def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("workflow",))
    parser.add_argument("workflow_action", choices=("status", "explain", "resume", "stage", "parent", "lifecycle"))
    parser.add_argument("--workflow-root", required=True)
    parser.add_argument("--workflow-id", required=True)
    parser.add_argument("--target")
    parser.add_argument("--evidence")
    return parser

def _review_lifecycle_evidence(root: Path, workflow_id: str) -> dict[str, Any]:
    """Return native reviewer facts plus the exact CEK state they must review."""

    from runtime.workflow.command import load_ledger
    from runtime.workflow.coordinator import WorkflowCoordinator
    from runtime.workflow.lifecycle import extract_reviewer_lifecycle

    observed = extract_reviewer_lifecycle(root, workflow_id)
    coordinator = WorkflowCoordinator.load(load_ledger(root, workflow_id))
    candidate = coordinator.green_candidate
    reviewer_asset_sha = coordinator.reviewer_asset_sha
    if candidate is None or not reviewer_asset_sha:
        raise LifecycleError("reviewer lifecycle has no current GREEN candidate or reviewer asset")
    return {
        **observed,
        "candidate": candidate.to_payload(),
        "reviewerAssetSha": reviewer_asset_sha,
    }


def _workflow_main(args: argparse.Namespace) -> dict[str, Any]:
    from runtime.workflow.command import (
        explain_workflow,
        record_transition,
        resume_workflow,
        workflow_status,
    )
    from runtime.workflow.model import CandidateIdentity, WorkflowState

    if not args.workflow_action:
        raise LifecycleError("WORKFLOW_ACTION_REQUIRED: choose status, explain, resume, stage, parent, or lifecycle")
    if not args.workflow_root or not args.workflow_id:
        raise LifecycleError("WORKFLOW_IDENTITY_REQUIRED: provide --workflow-root and --workflow-id")
    root = Path(args.workflow_root)
    if args.workflow_action == "status":
        return workflow_status(root, args.workflow_id)
    if args.workflow_action == "explain":
        return explain_workflow(root, args.workflow_id)
    if args.workflow_action == "parent":
        from runtime.workflow.lifecycle import extract_parent_identity

        return extract_parent_identity(root, args.workflow_id)
    if args.workflow_action == "lifecycle":
        return _review_lifecycle_evidence(root, args.workflow_id)
    if args.workflow_action in {"stage", "resume"}:
        if not args.evidence:
            raise LifecycleError("WORKFLOW_EVIDENCE_REQUIRED: provide a local JSON --evidence file")
        payload = _load_json(Path(args.evidence), "workflow evidence")
        if args.workflow_action == "stage":
            if not args.target:
                raise LifecycleError("WORKFLOW_TARGET_REQUIRED: provide --target")
            try:
                target = WorkflowState(args.target)
            except ValueError as exc:
                raise LifecycleError(f"unknown workflow target: {args.target}") from exc
            if target in {WorkflowState.REVIEW_ACCEPTED, WorkflowState.REVIEW_REJECTED}:
                from runtime.workflow.lifecycle import extract_reviewer_lifecycle

                observed = extract_reviewer_lifecycle(root, args.workflow_id)
                native_fields = (
                    "source",
                    "startEvent",
                    "stopEvent",
                    "parentIdentity",
                    "startChildIdentity",
                    "stopChildIdentity",
                    "childIdentity",
                    "resultSourceChildIdentity",
                    "agentType",
                    "structuredResult",
                )
                if any(payload.get(field) != observed.get(field) for field in native_fields):
                    raise LifecycleError("review evidence does not match native child output")
            return record_transition(root, args.workflow_id, target, payload)
        try:
            candidate = CandidateIdentity.from_payload(payload["candidate"])
            worktree_id = str(payload["worktreeId"])
        except (KeyError, ValueError) as exc:
            raise LifecycleError("resume evidence requires a valid candidate and worktreeId") from exc
        return resume_workflow(root, args.workflow_id, candidate, worktree_id)
    raise LifecycleError("WORKFLOW_API_AUTHORITY_REQUIRED: native execution requires an explicit caller-supplied authorization provider")

def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = _workflow_main(args)
    except (ValueError, OSError) as error:
        print(json.dumps({"status": "BLOCKED", "errorType": type(error).__name__}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
