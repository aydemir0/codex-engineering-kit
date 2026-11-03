from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class WorkflowState(str, Enum):
    CREATED = "CREATED"
    CLASSIFIED = "CLASSIFIED"
    PLANNED = "PLANNED"
    ISOLATION_READY = "ISOLATION_READY"
    RED_REQUIRED = "RED_REQUIRED"
    RED_CONFIRMED = "RED_CONFIRMED"
    IMPLEMENTING = "IMPLEMENTING"
    GREEN_REQUIRED = "GREEN_REQUIRED"
    GREEN_CONFIRMED = "GREEN_CONFIRMED"
    REVIEW_REQUESTED = "REVIEW_REQUESTED"
    REVIEW_RUNNING = "REVIEW_RUNNING"
    REVIEW_ACCEPTED = "REVIEW_ACCEPTED"
    REVIEW_REJECTED = "REVIEW_REJECTED"
    REWORK_REQUIRED = "REWORK_REQUIRED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"
    ABORTED = "ABORTED"
    CLEANUP_PENDING = "CLEANUP_PENDING"
    CLOSED = "CLOSED"


class FailureClass(str, Enum):
    F1_PLANNING = "F1"
    F2_IMPLEMENTATION = "F2"
    F3_TEST_REGRESSION = "F3"
    F4_TOOL_RUNTIME = "F4"
    F5_LIFECYCLE = "F5"
    F6_REVIEWER = "F6"
    F7_SECURITY = "F7"
    F8_CONTEXT_EXHAUSTION = "F8"
    F9_TIMEOUT = "F9"
    F10_HUMAN_INTERVENTION = "F10"
    F11_INFRASTRUCTURE_QUOTA = "F11"


class CleanupDisposition(str, Enum):
    REMOVED = "REMOVED"
    RETAINED_BY_POLICY = "RETAINED_BY_POLICY"


REQUIRED_VERIFICATION_DIMENSIONS = (
    "FUNCTIONAL",
    "TEST",
    "REVIEW",
    "LIFECYCLE",
    "EVIDENCE",
    "SECURITY",
)


@dataclass(frozen=True)
class CandidateIdentity:
    base_commit_sha: str
    candidate_commit_sha: str | None
    candidate_tree_oid: str
    candidate_manifest_digest: str
    candidate_diff_digest: str
    file_set_digest: str
    worktree_id: str
    branch: str | None
    dirty: bool

    def __post_init__(self) -> None:
        for label, value, pattern in (
            ("base commit", self.base_commit_sha, SHA40),
            ("candidate tree", self.candidate_tree_oid, SHA40),
            ("candidate manifest", self.candidate_manifest_digest, SHA256),
            ("candidate diff", self.candidate_diff_digest, SHA256),
            ("file set", self.file_set_digest, SHA256),
        ):
            if pattern.fullmatch(value) is None:
                raise ValueError(f"invalid {label} identity")
        if self.candidate_commit_sha is not None and SHA40.fullmatch(self.candidate_commit_sha) is None:
            raise ValueError("invalid candidate commit identity")
        if self.dirty and self.candidate_commit_sha is not None:
            raise ValueError("dirty candidate cannot claim a candidate commit")
        if not self.worktree_id:
            raise ValueError("candidate requires a worktree identity")

    def to_payload(self) -> dict[str, Any]:
        return {
            "baseCommitSha": self.base_commit_sha,
            "candidateCommitSha": self.candidate_commit_sha,
            "candidateTreeOid": self.candidate_tree_oid,
            "candidateManifestDigest": self.candidate_manifest_digest,
            "candidateDiffDigest": self.candidate_diff_digest,
            "fileSetDigest": self.file_set_digest,
            "worktreeId": self.worktree_id,
            "branch": self.branch,
            "dirty": self.dirty,
        }

    @classmethod
    def from_payload(cls, value: object) -> "CandidateIdentity":
        if not isinstance(value, dict):
            raise ValueError("candidate identity must be an object")
        try:
            return cls(
                base_commit_sha=str(value["baseCommitSha"]),
                candidate_commit_sha=str(value["candidateCommitSha"]) if value.get("candidateCommitSha") else None,
                candidate_tree_oid=str(value["candidateTreeOid"]),
                candidate_manifest_digest=str(value["candidateManifestDigest"]),
                candidate_diff_digest=str(value["candidateDiffDigest"]),
                file_set_digest=str(value["fileSetDigest"]),
                worktree_id=str(value["worktreeId"]),
                branch=str(value["branch"]) if value.get("branch") else None,
                dirty=value["dirty"] is True,
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("candidate identity is invalid") from exc


def json_safe(value: Any) -> Any:
    if isinstance(value, CandidateIdentity):
        return value.to_payload()
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: json_safe(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value
