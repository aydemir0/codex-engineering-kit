from __future__ import annotations

from collections.abc import Mapping
import hashlib
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from runtime.assurance.model import Permission

from .ledger import WorkflowLedger
from .model import (
    REQUIRED_VERIFICATION_DIMENSIONS,
    CandidateIdentity,
    FailureClass,
    WorkflowState,
    json_safe,
)


class TransitionError(ValueError):
    pass


class StaleWorkflowError(TransitionError):
    pass


ALLOWED: dict[WorkflowState, set[WorkflowState]] = {
    WorkflowState.CREATED: {WorkflowState.CLASSIFIED},
    WorkflowState.CLASSIFIED: {WorkflowState.PLANNED},
    WorkflowState.PLANNED: {WorkflowState.ISOLATION_READY},
    WorkflowState.ISOLATION_READY: {WorkflowState.RED_REQUIRED},
    WorkflowState.RED_REQUIRED: {WorkflowState.RED_CONFIRMED},
    WorkflowState.RED_CONFIRMED: {WorkflowState.IMPLEMENTING},
    WorkflowState.IMPLEMENTING: {WorkflowState.GREEN_REQUIRED},
    WorkflowState.GREEN_REQUIRED: {WorkflowState.GREEN_CONFIRMED},
    WorkflowState.GREEN_CONFIRMED: {WorkflowState.REVIEW_REQUESTED},
    WorkflowState.REVIEW_REQUESTED: {WorkflowState.REVIEW_RUNNING},
    WorkflowState.REVIEW_RUNNING: {WorkflowState.REVIEW_ACCEPTED, WorkflowState.REVIEW_REJECTED},
    WorkflowState.REVIEW_REJECTED: {WorkflowState.REWORK_REQUIRED},
    WorkflowState.REVIEW_ACCEPTED: {WorkflowState.VERIFYING},
    WorkflowState.VERIFYING: {WorkflowState.VERIFIED},
    WorkflowState.VERIFIED: {WorkflowState.CLEANUP_PENDING},
    WorkflowState.BLOCKED: {WorkflowState.CLEANUP_PENDING},
    WorkflowState.FAILED: {WorkflowState.CLEANUP_PENDING},
    WorkflowState.ABORTED: {WorkflowState.CLEANUP_PENDING},
    WorkflowState.CLEANUP_PENDING: {WorkflowState.CLOSED},
}

TERMINAL_INPUT_STATES = {WorkflowState.CLOSED}
EXTERNAL_EFFECTS = {"push", "merge", "tag", "release", "publish", "deploy", "submit"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(json_safe(value), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def _candidate(value: object) -> CandidateIdentity | None:
    if isinstance(value, CandidateIdentity):
        return value
    try:
        return CandidateIdentity.from_payload(value)
    except ValueError:
        return None


def require_m2a_authority(authority: object) -> None:
    authorize = getattr(authority, "authorize", None)
    if not callable(authorize):
        raise TransitionError("WORKFLOW_AUTHORITY_REQUIRED")
    for permission in (Permission.ORCHESTRATION, Permission.MANAGED_WORKTREE):
        decision = authorize(permission)
        permissions = getattr(decision, "permissions", None)
        if not isinstance(permissions, Mapping) or permissions.get(permission) is not True:
            raise TransitionError(f"M2A authority denied {permission.value}")


class WorkflowCoordinator:
    def __init__(
        self,
        *,
        ledger: WorkflowLedger,
        workflow_id: str,
        attempt_id: str,
        task_digest: str,
        base_commit_sha: str,
        cek_sha: str,
        runtime_identity: dict[str, Any],
        state: WorkflowState = WorkflowState.CREATED,
        retry_of: str | None = None,
        current_candidate: CandidateIdentity | None = None,
    ):
        self.ledger = ledger
        self.workflow_id = workflow_id
        self.attempt_id = attempt_id
        self.task_digest = task_digest
        self.base_commit_sha = base_commit_sha
        self.cek_sha = cek_sha
        self.runtime_identity = runtime_identity
        self.state = state
        self.retry_of = retry_of
        self.current_candidate = current_candidate
        self.green_candidate: CandidateIdentity | None = None
        self.review_candidate: CandidateIdentity | None = None
        self.verified_candidate: CandidateIdentity | None = None
        self.parent_identity: str | None = None
        self.reviewer_asset_sha: str | None = None

    @classmethod
    def create(cls, **kwargs: Any) -> "WorkflowCoordinator":
        if any(event.get("attemptId") == kwargs.get("attempt_id") for event in kwargs["ledger"].events):
            raise TransitionError("WORKFLOW_ATTEMPT_ALREADY_EXISTS")
        coordinator = cls(**kwargs)
        coordinator._append(WorkflowState.CREATED, "ACCEPTED", {"created": True}, state_from=None)
        return coordinator

    @classmethod
    def load(cls, ledger: WorkflowLedger) -> "WorkflowCoordinator":
        if not ledger.events:
            raise TransitionError("WORKFLOW_LEDGER_EMPTY")
        workflow_ids = {event.get("workflowId") for event in ledger.events}
        if len(workflow_ids) != 1 or None in workflow_ids:
            raise TransitionError("WORKFLOW_LEDGER_MIXED_IDENTITIES")
        accepted = [event for event in ledger.events
                    if event.get("result") == "ACCEPTED"
                    or (event.get("result") in {"FAIL", "BLOCKED"}
                        and event.get("stateTo") in {"FAILED", "BLOCKED"}
                        and event.get("isDirectFailure") is True)]
        if not accepted:
            raise TransitionError("WORKFLOW_LEDGER_HAS_NO_ACCEPTED_STATE")
        first = accepted[0]
        attempt_id = str(accepted[-1].get("attemptId"))
        attempt_events = [event for event in accepted if event.get("attemptId") == attempt_id]
        if not attempt_events:
            raise TransitionError("WORKFLOW_ATTEMPT_MISSING")
        last = attempt_events[-1]
        try:
            state = WorkflowState(str(last["stateTo"]))
            coordinator = cls(
                ledger=ledger,
                workflow_id=str(first["workflowId"]),
                attempt_id=attempt_id,
                task_digest=str(first["taskDigest"]),
                base_commit_sha=str(first["baseSha"]),
                cek_sha=str(first["cekSha"]),
                runtime_identity=dict(first["runtimeIdentity"]),
                state=state,
                retry_of=last.get("retry_of"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TransitionError("WORKFLOW_LEDGER_STATE_INVALID") from exc
        for event in attempt_events:
            target = WorkflowState(str(event["stateTo"]))
            evidence = event.get("evidence")
            if isinstance(evidence, dict):
                coordinator._apply(target, evidence)
        return coordinator

    def _append(
        self,
        state_to: WorkflowState | None,
        result: str,
        evidence: dict[str, Any],
        *,
        state_from: WorkflowState | None = None,
        **extra: Any,
    ) -> dict[str, Any]:
        return self.ledger.append({
            "schemaVersion": 1,
            "workflowId": self.workflow_id,
            "attemptId": self.attempt_id,
            "eventId": f"event-{uuid4().hex}",
            "timestampUtc": _now(),
            "retry_of": self.retry_of,
            "stateFrom": (self.state if state_from is None else state_from).value if (self.state if state_from is None else state_from) is not None else None,
            "stateTo": state_to.value if state_to is not None else None,
            "result": result,
            "taskDigest": self.task_digest,
            "baseSha": self.base_commit_sha,
            "runtimeIdentity": self.runtime_identity,
            "cekSha": self.cek_sha,
            "evidence": evidence,
            **extra,
        })

    def _reject(self, target: WorkflowState, evidence: dict[str, Any], reason: str) -> None:
        self._append(target, "REJECTED", evidence, reasonCode=reason, failureClass=FailureClass.F5_LIFECYCLE.value)
        raise TransitionError(reason)

    def advance(self, target: WorkflowState, evidence: dict[str, Any]) -> dict[str, Any]:
        if self.state in TERMINAL_INPUT_STATES or target not in ALLOWED.get(self.state, set()):
            self._reject(target, evidence, "INVALID_TRANSITION")
        try:
            self._validate(target, evidence)
        except TransitionError as exc:
            self._reject(target, evidence, str(exc))
        previous = self.state
        row = self._append(target, "ACCEPTED", evidence, state_from=previous)
        self.state = target
        self._apply(target, evidence)
        return row

    def _validate(self, target: WorkflowState, evidence: dict[str, Any]) -> None:
        if target is WorkflowState.CLASSIFIED:
            classification = evidence.get("classification")
            required = {"taskClass", "risk", "tools", "tests", "review"}
            if not isinstance(classification, dict) or not required.issubset(classification):
                raise TransitionError("CLASSIFICATION_INCOMPLETE")
        elif target is WorkflowState.PLANNED:
            plan = evidence.get("plan")
            required = {"goal", "scope", "redStrategy", "commands", "reviewer", "security", "recovery"}
            if not isinstance(plan, dict) or not required.issubset(plan):
                raise TransitionError("PLAN_INCOMPLETE")
        elif target is WorkflowState.ISOLATION_READY:
            candidate = _candidate(evidence.get("candidate"))
            if evidence.get("authorized") is not True or candidate is None or evidence.get("worktreeId") != candidate.worktree_id:
                raise TransitionError("ISOLATION_EVIDENCE_INVALID")
            if candidate.base_commit_sha != self.base_commit_sha:
                raise TransitionError("BASE_CANDIDATE_MISMATCH")
        elif target is WorkflowState.RED_CONFIRMED:
            candidate = _candidate(evidence.get("candidate"))
            if evidence.get("result") != "FAIL" or evidence.get("failureKind") != "BEHAVIOR":
                raise TransitionError("RED_NOT_TASK_RELEVANT")
            if not evidence.get("commandDigest") or not evidence.get("expectedSignature"):
                raise TransitionError("RED_EVIDENCE_INCOMPLETE")
            if candidate != self.current_candidate or evidence.get("worktreeId") != getattr(candidate, "worktree_id", None):
                raise TransitionError("RED_SUBJECT_MISMATCH")
        elif target is WorkflowState.GREEN_CONFIRMED:
            candidate = _candidate(evidence.get("candidate"))
            if evidence.get("result") != "PASS" or evidence.get("fresh") is not True or not evidence.get("commandDigest"):
                raise TransitionError("GREEN_NOT_FRESH")
            if candidate is None or candidate.worktree_id != evidence.get("worktreeId"):
                raise TransitionError("GREEN_SUBJECT_MISMATCH")
        elif target is WorkflowState.REVIEW_RUNNING:
            candidate = _candidate(evidence.get("candidate"))
            if candidate != self.green_candidate or not evidence.get("parentIdentity") or not evidence.get("reviewerAssetSha"):
                raise TransitionError("REVIEW_INPUT_INVALID")
        elif target in {WorkflowState.REVIEW_ACCEPTED, WorkflowState.REVIEW_REJECTED}:
            self._validate_review(target, evidence)
        elif target is WorkflowState.VERIFIED:
            candidate = _candidate(evidence.get("candidate"))
            dimensions = evidence.get("dimensions")
            if candidate != self.review_candidate:
                raise TransitionError("VERIFICATION_CANDIDATE_MISMATCH")
            if not isinstance(dimensions, dict) or set(dimensions) != set(REQUIRED_VERIFICATION_DIMENSIONS):
                raise TransitionError("VERIFICATION_DIMENSIONS_INCOMPLETE")
            if any(dimensions[name] not in {"PASS", "NOT_APPLICABLE"} for name in REQUIRED_VERIFICATION_DIMENSIONS):
                raise TransitionError("VERIFICATION_DIMENSION_NOT_PASSING")
        elif target is WorkflowState.CLOSED:
            disposition = evidence.get("cleanupDisposition")
            if disposition not in {"REMOVED", "RETAINED_BY_POLICY"}:
                raise TransitionError("CLEANUP_NOT_COMPLETE")
            if disposition == "RETAINED_BY_POLICY" and not evidence.get("recoveryGuidance"):
                raise TransitionError("RETAINED_RESOURCE_REQUIRES_GUIDANCE")

    def _validate_review(self, target: WorkflowState, evidence: dict[str, Any]) -> None:
        candidate = _candidate(evidence.get("candidate"))
        parent = evidence.get("parentIdentity")
        start = evidence.get("startChildIdentity")
        stop = evidence.get("stopChildIdentity")
        child = evidence.get("childIdentity")
        structured = evidence.get("structuredResult")
        if candidate != self.green_candidate:
            raise TransitionError("REVIEW_CANDIDATE_MISMATCH")
        if parent != self.parent_identity or not child or child == parent:
            raise TransitionError("REVIEW_PARENT_CHILD_MISMATCH")
        if start != child or stop != child:
            raise TransitionError("REVIEW_LIFECYCLE_MISMATCH")
        if evidence.get("resultSourceChildIdentity") != child:
            raise TransitionError("REVIEW_RESULT_SOURCE_MISMATCH")
        if evidence.get("agentType") != "reviewer" or evidence.get("reviewerAssetSha") != self.reviewer_asset_sha:
            raise TransitionError("REVIEW_ROLE_OR_ASSET_MISMATCH")
        if not isinstance(structured, dict) or not isinstance(structured.get("findings"), list):
            raise TransitionError("REVIEW_RESULT_UNSTRUCTURED")
        if structured.get("role") != "reviewer":
            raise TransitionError("REVIEW_RESULT_ROLE_MISMATCH")
        if (
            structured.get("candidateManifestDigest") != candidate.candidate_manifest_digest
            or structured.get("candidateTreeOid") != candidate.candidate_tree_oid
        ):
            raise TransitionError("REVIEW_RESULT_CANDIDATE_MISMATCH")
        blocking = any(isinstance(finding, dict) and finding.get("blocking") is True for finding in structured["findings"])
        if target is WorkflowState.REVIEW_ACCEPTED and (structured.get("disposition") != "ACCEPT" or blocking):
            raise TransitionError("REVIEW_BLOCKING_FINDING")
        if target is WorkflowState.REVIEW_REJECTED and structured.get("disposition") != "REJECT":
            raise TransitionError("REVIEW_REJECTION_INVALID")

    def _apply(self, target: WorkflowState, evidence: dict[str, Any]) -> None:
        if target is WorkflowState.ISOLATION_READY:
            self.current_candidate = _candidate(evidence.get("candidate"))
        elif target is WorkflowState.GREEN_CONFIRMED:
            self.current_candidate = _candidate(evidence.get("candidate"))
            self.green_candidate = self.current_candidate
        elif target is WorkflowState.REVIEW_RUNNING:
            self.parent_identity = str(evidence["parentIdentity"])
            self.reviewer_asset_sha = str(evidence["reviewerAssetSha"])
        elif target is WorkflowState.REVIEW_ACCEPTED:
            self.review_candidate = _candidate(evidence.get("candidate"))
        elif target is WorkflowState.VERIFIED:
            self.verified_candidate = _candidate(evidence.get("candidate"))

    def is_green_current(self, candidate: CandidateIdentity) -> bool:
        return self.green_candidate == candidate

    def review_is_current(self, candidate: CandidateIdentity) -> bool:
        return self.review_candidate == candidate

    def verification_is_current(self, candidate: CandidateIdentity) -> bool:
        return self.verified_candidate == candidate

    def fail(self, failure_class: FailureClass, reason_code: str) -> dict[str, Any]:
        if self.state in {WorkflowState.VERIFIED, WorkflowState.FAILED, WorkflowState.BLOCKED, WorkflowState.ABORTED, WorkflowState.CLEANUP_PENDING, WorkflowState.CLOSED}:
            raise TransitionError("WORKFLOW_EXECUTION_TERMINAL")
        previous = self.state
        event_id = f"event-{uuid4().hex}"
        row = self.ledger.append({
            "schemaVersion": 1,
            "workflowId": self.workflow_id,
            "attemptId": self.attempt_id,
            "eventId": event_id,
            "timestampUtc": _now(),
            "retry_of": self.retry_of,
            "stateFrom": previous.value,
            "stateTo": WorkflowState.FAILED.value,
            "result": "FAIL",
            "failureClass": failure_class.value,
            "reasonCode": reason_code,
            "taskDigest": self.task_digest,
            "baseSha": self.base_commit_sha,
            "runtimeIdentity": self.runtime_identity,
            "cekSha": self.cek_sha,
            "evidence": {},
            "rootFailureEventId": event_id,
            "causedByEventId": None,
            "isDirectFailure": True,
        })
        self.state = WorkflowState.FAILED
        return row

    def block(self, failure_class: FailureClass, reason_code: str) -> dict[str, Any]:
        if self.state in {WorkflowState.VERIFIED, WorkflowState.FAILED, WorkflowState.BLOCKED, WorkflowState.ABORTED, WorkflowState.CLEANUP_PENDING, WorkflowState.CLOSED}:
            raise TransitionError("WORKFLOW_EXECUTION_TERMINAL")
        previous = self.state
        event_id = f"event-{uuid4().hex}"
        row = self.ledger.append({
            "schemaVersion": 1,
            "workflowId": self.workflow_id,
            "attemptId": self.attempt_id,
            "eventId": event_id,
            "timestampUtc": _now(),
            "retry_of": self.retry_of,
            "stateFrom": previous.value,
            "stateTo": WorkflowState.BLOCKED.value,
            "result": "BLOCKED",
            "failureClass": failure_class.value,
            "reasonCode": reason_code,
            "taskDigest": self.task_digest,
            "baseSha": self.base_commit_sha,
            "runtimeIdentity": self.runtime_identity,
            "cekSha": self.cek_sha,
            "evidence": {},
            "rootFailureEventId": event_id,
            "causedByEventId": None,
            "isDirectFailure": True,
        })
        self.state = WorkflowState.BLOCKED
        return row

    def record_dependency_block(self, stage: str, root_failure_event_id: str) -> dict[str, Any]:
        return self._append(None, "BLOCKED", {"stage": stage}, failureClass=None, reasonCode="DEPENDENCY_BLOCKED", rootFailureEventId=root_failure_event_id, causedByEventId=root_failure_event_id, isDirectFailure=False)

    def retry(self, attempt_id: str) -> "WorkflowCoordinator":
        if self.state not in {WorkflowState.FAILED, WorkflowState.BLOCKED, WorkflowState.ABORTED}:
            raise TransitionError("WORKFLOW_RETRY_REQUIRES_STOPPED_ATTEMPT")
        if self.state in {WorkflowState.VERIFIED, WorkflowState.CLEANUP_PENDING, WorkflowState.CLOSED}:
            raise TransitionError("WORKFLOW_EXECUTION_TERMINAL")
        return WorkflowCoordinator.create(
            ledger=self.ledger,
            workflow_id=self.workflow_id,
            attempt_id=attempt_id,
            task_digest=self.task_digest,
            base_commit_sha=self.base_commit_sha,
            cek_sha=self.cek_sha,
            runtime_identity=self.runtime_identity,
            retry_of=self.attempt_id,
        )

    def start_rework(self, attempt_id: str, candidate: CandidateIdentity) -> "WorkflowCoordinator":
        if any(event.get("attemptId") == attempt_id for event in self.ledger.events):
            raise TransitionError("WORKFLOW_ATTEMPT_ALREADY_EXISTS")
        if self.state is not WorkflowState.REWORK_REQUIRED or candidate == self.current_candidate:
            raise TransitionError("REWORK_CANDIDATE_REQUIRED")
        coordinator = WorkflowCoordinator(
            ledger=self.ledger,
            workflow_id=self.workflow_id,
            attempt_id=attempt_id,
            task_digest=self.task_digest,
            base_commit_sha=self.base_commit_sha,
            cek_sha=self.cek_sha,
            runtime_identity=self.runtime_identity,
            state=WorkflowState.IMPLEMENTING,
            retry_of=self.attempt_id,
            current_candidate=candidate,
        )
        coordinator._append(WorkflowState.IMPLEMENTING, "ACCEPTED", {"candidate": candidate, "rework": True}, state_from=WorkflowState.REWORK_REQUIRED)
        return coordinator

    def resume(self, candidate: CandidateIdentity, worktree_id: str) -> None:
        if self.state in {WorkflowState.VERIFIED, WorkflowState.FAILED, WorkflowState.BLOCKED, WorkflowState.ABORTED, WorkflowState.CLEANUP_PENDING, WorkflowState.CLOSED}:
            raise TransitionError("WORKFLOW_EXECUTION_TERMINAL")
        if self.current_candidate != candidate or candidate.worktree_id != worktree_id:
            raise StaleWorkflowError("RESUME_SUBJECT_STALE")

    @staticmethod
    def external_action_allowed(action: str) -> bool:
        return action.casefold() not in EXTERNAL_EFFECTS

    @staticmethod
    def required_agent_roles() -> tuple[str, ...]:
        return ("reviewer",)

    def runtime_candidate_record(self, candidate: CandidateIdentity, *, evidence_closure_sha: str | None) -> dict[str, Any]:
        return {**candidate.to_payload(), "evidenceOnlyClosureSha": evidence_closure_sha}
