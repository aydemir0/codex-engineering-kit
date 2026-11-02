from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock


SHA40 = "a" * 40
SHA256 = "b" * 64


class M2BContractTests(unittest.TestCase):
    """The numbered methods map one-to-one to the frozen M2B RED contract."""

    def setUp(self) -> None:
        self.model = importlib.import_module("runtime.workflow.model")
        self.ledger_module = importlib.import_module("runtime.workflow.ledger")
        self.coordinator_module = importlib.import_module("runtime.workflow.coordinator")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.ledger = self.ledger_module.WorkflowLedger(self.root / "ledger.json")
        self.coordinator = self.coordinator_module.WorkflowCoordinator.create(
            ledger=self.ledger,
            workflow_id="workflow-1",
            attempt_id="attempt-1",
            task_digest=SHA256,
            base_commit_sha=SHA40,
            cek_sha="c" * 40,
            runtime_identity={"version": "0.155.1", "binarySha256": "d" * 64},
        )

    def _classification(self) -> dict[str, object]:
        return {
            "taskClass": "BUG_FIX",
            "risk": "LOW",
            "tools": ["python"],
            "tests": ["python -B -m unittest test_bug.py"],
            "review": "reviewer",
        }

    def _plan(self) -> dict[str, object]:
        return {
            "goal": "fix the bounded fixture defect",
            "scope": ["src/bug.py", "test_bug.py"],
            "redStrategy": "add the missing regression and observe expected assertion failure",
            "commands": ["python -B -m unittest test_bug.py"],
            "reviewer": "reviewer",
            "security": "no network or external effects",
            "recovery": "retain failed attempt and owned worktree disposition",
        }

    def _candidate(self, digest: str = "e" * 64, *, dirty: bool = True) -> object:
        return self.model.CandidateIdentity(
            base_commit_sha=SHA40,
            candidate_commit_sha=None if dirty else "f" * 40,
            candidate_tree_oid="1" * 40,
            candidate_manifest_digest=digest,
            candidate_diff_digest="2" * 64,
            file_set_digest="3" * 64,
            worktree_id="worktree-1",
            branch="codex/worktree-1",
            dirty=dirty,
        )

    def _to_isolation(self) -> object:
        self.coordinator.advance(self.model.WorkflowState.CLASSIFIED, {"classification": self._classification()})
        self.coordinator.advance(self.model.WorkflowState.PLANNED, {"plan": self._plan()})
        self.coordinator.advance(
            self.model.WorkflowState.ISOLATION_READY,
            {"authorized": True, "worktreeId": "worktree-1", "candidate": self._candidate()},
        )
        return self.coordinator

    def _to_green(self, candidate: object | None = None) -> object:
        subject = candidate or self._candidate()
        self._to_isolation()
        self.coordinator.advance(self.model.WorkflowState.RED_REQUIRED, {})
        self.coordinator.advance(
            self.model.WorkflowState.RED_CONFIRMED,
            {
                "result": "FAIL",
                "failureKind": "BEHAVIOR",
                "commandDigest": "4" * 64,
                "expectedSignature": "AssertionError: 4 != 5",
                "candidate": subject,
                "worktreeId": "worktree-1",
            },
        )
        self.coordinator.advance(self.model.WorkflowState.IMPLEMENTING, {})
        self.coordinator.advance(self.model.WorkflowState.GREEN_REQUIRED, {})
        self.coordinator.advance(
            self.model.WorkflowState.GREEN_CONFIRMED,
            {
                "result": "PASS",
                "commandDigest": "4" * 64,
                "candidate": subject,
                "worktreeId": "worktree-1",
                "fresh": True,
            },
        )
        return subject

    def _to_review_running(self, candidate: object | None = None) -> object:
        subject = self._to_green(candidate)
        self.coordinator.advance(self.model.WorkflowState.REVIEW_REQUESTED, {})
        self.coordinator.advance(
            self.model.WorkflowState.REVIEW_RUNNING,
            {
                "candidate": subject,
                "parentIdentity": "parent-1",
                "reviewerAssetSha": "5" * 64,
            },
        )
        return subject

    def _review(self, candidate: object, **overrides: object) -> dict[str, object]:
        evidence: dict[str, object] = {
            "candidate": candidate,
            "parentIdentity": "parent-1",
            "startChildIdentity": "child-1",
            "stopChildIdentity": "child-1",
            "childIdentity": "child-1",
            "resultSourceChildIdentity": "child-1",
            "agentType": "reviewer",
            "reviewerAssetSha": "5" * 64,
            "structuredResult": {
                "disposition": "ACCEPT",
                "role": "reviewer",
                "findings": [],
                "candidateManifestDigest": candidate.candidate_manifest_digest,
                "candidateTreeOid": candidate.candidate_tree_oid,
            },
        }
        evidence.update(overrides)
        return evidence

    def _rejection(self, candidate: object, findings: list[dict[str, object]]) -> dict[str, object]:
        result = dict(self._review(candidate)["structuredResult"])
        result.update({"disposition": "REJECT", "findings": findings})
        return result

    def _to_review_accepted(self) -> object:
        subject = self._to_review_running()
        self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(subject))
        return subject

    def test_01_workflow_cannot_skip_classify(self) -> None:
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.PLANNED, {"plan": self._plan()})

    def test_02_workflow_cannot_skip_plan(self) -> None:
        self.coordinator.advance(self.model.WorkflowState.CLASSIFIED, {"classification": self._classification()})
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.ISOLATION_READY, {})

    def test_03_isolation_is_required_before_red_or_implementation(self) -> None:
        self.coordinator.advance(self.model.WorkflowState.CLASSIFIED, {"classification": self._classification()})
        self.coordinator.advance(self.model.WorkflowState.PLANNED, {"plan": self._plan()})
        for state in (self.model.WorkflowState.RED_REQUIRED, self.model.WorkflowState.IMPLEMENTING):
            with self.assertRaises(self.coordinator_module.TransitionError):
                self.coordinator.advance(state, {})

    def test_04_red_rejects_infrastructure_failure(self) -> None:
        self._to_isolation()
        self.coordinator.advance(self.model.WorkflowState.RED_REQUIRED, {})
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(
                self.model.WorkflowState.RED_CONFIRMED,
                {"result": "FAIL", "failureKind": "INFRASTRUCTURE", "candidate": self._candidate(), "worktreeId": "worktree-1"},
            )

    def test_05_red_is_bound_to_candidate_and_worktree(self) -> None:
        self._to_isolation()
        self.coordinator.advance(self.model.WorkflowState.RED_REQUIRED, {})
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(
                self.model.WorkflowState.RED_CONFIRMED,
                {"result": "FAIL", "failureKind": "BEHAVIOR", "candidate": self._candidate("9" * 64), "worktreeId": "foreign"},
            )

    def test_06_implementation_requires_valid_red(self) -> None:
        self._to_isolation()
        self.coordinator.advance(self.model.WorkflowState.RED_REQUIRED, {})
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.IMPLEMENTING, {})

    def test_07_green_must_be_fresh(self) -> None:
        self._to_isolation()
        self.coordinator.advance(self.model.WorkflowState.RED_REQUIRED, {})
        subject = self._candidate()
        self.coordinator.advance(self.model.WorkflowState.RED_CONFIRMED, {"result": "FAIL", "failureKind": "BEHAVIOR", "commandDigest": "4" * 64, "expectedSignature": "failure", "candidate": subject, "worktreeId": "worktree-1"})
        self.coordinator.advance(self.model.WorkflowState.IMPLEMENTING, {})
        self.coordinator.advance(self.model.WorkflowState.GREEN_REQUIRED, {})
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.GREEN_CONFIRMED, {"result": "PASS", "fresh": False, "candidate": subject, "worktreeId": "worktree-1"})

    def test_08_green_stales_after_candidate_mutation(self) -> None:
        self._to_green()
        self.assertFalse(self.coordinator.is_green_current(self._candidate("8" * 64)))

    def test_09_parent_self_review_is_rejected(self) -> None:
        subject = self._to_review_running()
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(subject, childIdentity="parent-1", startChildIdentity="parent-1", stopChildIdentity="parent-1"))

    def test_10_reviewer_config_presence_is_not_review_evidence(self) -> None:
        subject = self._to_review_running()
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, {"candidate": subject, "reviewerConfigPresent": True})

    def test_11_subagent_start_without_stop_is_rejected(self) -> None:
        subject = self._to_review_running()
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(subject, stopChildIdentity=None))

    def test_12_wrong_child_stop_is_rejected(self) -> None:
        subject = self._to_review_running()
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(subject, stopChildIdentity="child-2"))

    def test_13_reviewer_candidate_mismatch_is_rejected(self) -> None:
        subject = self._to_review_running()
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(self._candidate("8" * 64)))

    def test_14_parent_child_correlation_mismatch_is_rejected(self) -> None:
        subject = self._to_review_running()
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(subject, parentIdentity="wrong-parent"))

    def test_15_blocking_review_finding_prevents_acceptance(self) -> None:
        subject = self._to_review_running()
        result = {
            "disposition": "REJECT",
            "role": "reviewer",
            "findings": [{"severity": "HIGH", "evidence": "bug", "blocking": True}],
            "candidateManifestDigest": subject.candidate_manifest_digest,
            "candidateTreeOid": subject.candidate_tree_oid,
        }
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.REVIEW_ACCEPTED, self._review(subject, structuredResult=result))

    def test_15a_parent_supplied_result_for_other_candidate_is_rejected(self) -> None:
        subject = self._to_review_running()
        forged = dict(self._review(subject)["structuredResult"])
        forged["candidateManifestDigest"] = "9" * 64
        with self.assertRaisesRegex(self.coordinator_module.TransitionError, "REVIEW_RESULT_CANDIDATE_MISMATCH"):
            self.coordinator.advance(
                self.model.WorkflowState.REVIEW_ACCEPTED,
                self._review(subject, structuredResult=forged),
            )

    def test_15b_review_result_must_come_from_correlated_child(self) -> None:
        subject = self._to_review_running()
        with self.assertRaisesRegex(self.coordinator_module.TransitionError, "REVIEW_RESULT_SOURCE_MISMATCH"):
            self.coordinator.advance(
                self.model.WorkflowState.REVIEW_ACCEPTED,
                self._review(subject, resultSourceChildIdentity="other-child"),
            )

    def test_16_rejected_review_is_retained(self) -> None:
        subject = self._to_review_running()
        findings = [{"severity": "HIGH", "evidence": "bug", "blocking": True}]
        self.coordinator.advance(self.model.WorkflowState.REVIEW_REJECTED, self._review(subject, structuredResult=self._rejection(subject, findings)))
        self.assertEqual(self.ledger.events[-1]["evidence"]["structuredResult"]["findings"], findings)

    def test_17_rework_creates_new_candidate_identity(self) -> None:
        subject = self._to_review_running()
        self.coordinator.advance(self.model.WorkflowState.REVIEW_REJECTED, self._review(subject, structuredResult=self._rejection(subject, [{"blocking": True}])))
        self.coordinator.advance(self.model.WorkflowState.REWORK_REQUIRED, {})
        rework = self.coordinator.start_rework("attempt-2", self._candidate("7" * 64))
        self.assertNotEqual(rework.current_candidate, subject)
        self.assertEqual(rework.retry_of, "attempt-1")

    def test_18_rework_requires_fresh_green(self) -> None:
        subject = self._to_review_running()
        self.coordinator.advance(self.model.WorkflowState.REVIEW_REJECTED, self._review(subject, structuredResult=self._rejection(subject, [{"blocking": True}])))
        self.coordinator.advance(self.model.WorkflowState.REWORK_REQUIRED, {})
        rework = self.coordinator.start_rework("attempt-2", self._candidate("7" * 64))
        with self.assertRaises(self.coordinator_module.TransitionError):
            rework.advance(self.model.WorkflowState.REVIEW_REQUESTED, {})

    def test_19_rework_requires_fresh_review(self) -> None:
        subject = self._to_review_accepted()
        self.assertFalse(self.coordinator.review_is_current(self._candidate("7" * 64)))

    def test_20_failed_attempts_remain_retained(self) -> None:
        self.coordinator.fail(self.model.FailureClass.F3_TEST_REGRESSION, "GREEN_FAILED")
        retry = self.coordinator.retry("attempt-2")
        self.assertEqual(retry.retry_of, "attempt-1")
        self.assertTrue(any(event["attemptId"] == "attempt-1" and event["stateTo"] == "FAILED" for event in self.ledger.events))

    def test_21_dependency_block_is_not_direct_failure(self) -> None:
        root = self.coordinator.fail(self.model.FailureClass.F4_TOOL_RUNTIME, "RUNTIME_FAILED")
        blocked = self.coordinator.record_dependency_block("REVIEW", root["eventId"])
        self.assertFalse(blocked["isDirectFailure"])
        self.assertEqual(blocked["rootFailureEventId"], root["eventId"])

    def test_22_root_failure_is_not_multiplied(self) -> None:
        root = self.coordinator.fail(self.model.FailureClass.F3_TEST_REGRESSION, "RED_INVALID")
        self.coordinator.record_dependency_block("IMPLEMENT", root["eventId"])
        self.coordinator.record_dependency_block("REVIEW", root["eventId"])
        direct = [event for event in self.ledger.events if event.get("isDirectFailure")]
        self.assertEqual([event["eventId"] for event in direct], [root["eventId"]])

    def test_23_foreign_worktree_is_never_auto_deleted(self) -> None:
        native = importlib.import_module("runtime.workflow.native")
        remover = Mock()
        result = native.cleanup_worktree({"recordOwner": "thread-1", "liveOwner": "thread-2", "pathMatches": True}, remover)
        self.assertEqual(result, self.model.CleanupDisposition.RETAINED_BY_POLICY)
        remover.assert_not_called()

    def test_24_owned_worktree_requires_all_ownership_evidence(self) -> None:
        native = importlib.import_module("runtime.workflow.native")
        remover = Mock(return_value=True)
        incomplete = {"recordOwner": "thread-1", "liveOwner": None, "pathMatches": True}
        self.assertEqual(native.cleanup_worktree(incomplete, remover), self.model.CleanupDisposition.RETAINED_BY_POLICY)
        remover.assert_not_called()

    def test_25_cleanup_failure_prevents_closed(self) -> None:
        self.coordinator.fail(self.model.FailureClass.F3_TEST_REGRESSION, "TEST_FAILED")
        self.coordinator.advance(self.model.WorkflowState.CLEANUP_PENDING, {})
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.CLOSED, {"cleanupDisposition": "FAILED"})

    def test_26_retained_cleanup_resource_is_explicit(self) -> None:
        self.coordinator.fail(self.model.FailureClass.F5_LIFECYCLE, "FOREIGN_WORKTREE")
        self.coordinator.advance(self.model.WorkflowState.CLEANUP_PENDING, {})
        self.coordinator.advance(self.model.WorkflowState.CLOSED, {"cleanupDisposition": "RETAINED_BY_POLICY", "recoveryGuidance": "remove manually after ownership is established"})
        self.assertEqual(self.ledger.events[-1]["evidence"]["cleanupDisposition"], "RETAINED_BY_POLICY")

    def test_27_dirty_candidate_is_not_represented_by_head_sha(self) -> None:
        self.assertIsNone(self._candidate(dirty=True).candidate_commit_sha)

    def test_28_uncommitted_candidate_has_content_addressed_identity(self) -> None:
        candidate = self._candidate(dirty=True)
        self.assertRegex(candidate.candidate_tree_oid, r"^[0-9a-f]{40}$")
        self.assertRegex(candidate.candidate_manifest_digest, r"^[0-9a-f]{64}$")

    def test_29_candidate_capture_does_not_mutate_real_git_index(self) -> None:
        candidate_module = importlib.import_module("runtime.workflow.candidate")
        repository = self.root / "repo"
        repository.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repository, check=True)
        (repository / "a.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "a.txt"], cwd=repository, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=repository, check=True)
        index = repository / ".git" / "index"
        before = hashlib.sha256(index.read_bytes()).hexdigest()
        (repository / "a.txt").write_text("changed\n", encoding="utf-8")
        candidate_module.capture_candidate(repository, "worktree-1")
        self.assertEqual(hashlib.sha256(index.read_bytes()).hexdigest(), before)

    def test_30_candidate_manifest_is_immutable(self) -> None:
        candidate = self._candidate()
        with self.assertRaises((AttributeError, TypeError)):
            candidate.dirty = False

    def test_31_candidate_mutation_stales_review(self) -> None:
        self._to_review_accepted()
        self.assertFalse(self.coordinator.review_is_current(self._candidate("7" * 64)))

    def test_32_candidate_mutation_stales_final_verification(self) -> None:
        subject = self._to_review_accepted()
        self.coordinator.advance(self.model.WorkflowState.VERIFYING, {})
        dimensions = {name: "PASS" for name in self.model.REQUIRED_VERIFICATION_DIMENSIONS}
        self.coordinator.advance(self.model.WorkflowState.VERIFIED, {"candidate": subject, "dimensions": dimensions})
        self.assertFalse(self.coordinator.verification_is_current(self._candidate("7" * 64)))

    def test_33_candidate_capture_never_creates_a_commit(self) -> None:
        candidate_module = importlib.import_module("runtime.workflow.candidate")
        repository = self.root / "repo"
        repository.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repository, check=True)
        subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=repository, check=True)
        subprocess.run(["git", "config", "user.name", "Fixture"], cwd=repository, check=True)
        (repository / "a.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "add", "a.txt"], cwd=repository, check=True)
        subprocess.run(["git", "commit", "-qm", "base"], cwd=repository, check=True)
        before = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
        (repository / "a.txt").write_text("changed\n", encoding="utf-8")
        candidate_module.capture_candidate(repository, "worktree-1")
        after = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip()
        self.assertEqual(after, before)

    def test_34_normal_codex_home_cannot_be_disposable_profile(self) -> None:
        profile = importlib.import_module("runtime.workflow.profile")
        normal = self.root / "normal"
        normal.mkdir()
        with self.assertRaises(profile.WorkflowProfileError):
            profile.create_profile(normal, normal, self.root / "project", "workflow-1", "c" * 40)

    def test_35_secret_values_are_redacted_from_public_evidence(self) -> None:
        self.ledger.append_raw({"message": "Authorization: Bearer secret-token", "path": str(self.root / "private")})
        exported = json.dumps(self.ledger.sanitized_export(), sort_keys=True)
        self.assertNotIn("secret-token", exported)
        self.assertNotIn(str(self.root), exported)

    def test_36_auth_absence_is_blocked_not_product_failure(self) -> None:
        event = self.coordinator.block(self.model.FailureClass.F10_HUMAN_INTERVENTION, "M2B_AUTH_SETUP_REQUIRED")
        self.assertEqual(event["stateTo"], "BLOCKED")
        self.assertEqual(event["failureClass"], "F10")

    def test_37_external_effects_are_not_automatically_authorized(self) -> None:
        for action in ("push", "merge", "tag", "release", "publish"):
            self.assertFalse(self.coordinator.external_action_allowed(action))

    def test_38_resume_validates_actual_candidate(self) -> None:
        self._to_green()
        with self.assertRaises(self.coordinator_module.StaleWorkflowError):
            self.coordinator.resume(self._candidate("7" * 64), "worktree-1")

    def test_39_stale_persisted_state_fails_closed(self) -> None:
        self.ledger.path.write_text("{}\n", encoding="utf-8")
        with self.assertRaises(self.ledger_module.LedgerError):
            self.ledger_module.WorkflowLedger(self.ledger.path)

    def test_40_verified_requires_every_dimension(self) -> None:
        subject = self._to_review_accepted()
        self.coordinator.advance(self.model.WorkflowState.VERIFYING, {})
        dimensions = {name: "PASS" for name in self.model.REQUIRED_VERIFICATION_DIMENSIONS}
        dimensions["SECURITY"] = "BLOCKED"
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.VERIFIED, {"candidate": subject, "dimensions": dimensions})

    def test_41_raw_model_prose_cannot_create_pass(self) -> None:
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.CLASSIFIED, {"modelProse": "Everything passed"})

    def test_42_architecture_does_not_require_explorer(self) -> None:
        self.assertEqual(self.coordinator.required_agent_roles(), ("reviewer",))

    def test_43_ledger_retains_rejected_transitions(self) -> None:
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator.advance(self.model.WorkflowState.PLANNED, {})
        self.assertEqual(self.ledger.events[-1]["result"], "REJECTED")

    def test_44_runtime_identity_remains_m2a_governed(self) -> None:
        authority = Mock()
        authority.authorize.side_effect = [
            Mock(permissions={importlib.import_module("runtime.assurance.model").Permission.ORCHESTRATION: True}),
            Mock(permissions={importlib.import_module("runtime.assurance.model").Permission.MANAGED_WORKTREE: True}),
        ]
        self.coordinator_module.require_m2a_authority(authority)
        permissions = importlib.import_module("runtime.assurance.model").Permission
        self.assertEqual([call.args[0] for call in authority.authorize.call_args_list], [permissions.ORCHESTRATION, permissions.MANAGED_WORKTREE])

    def test_45_evidence_only_commit_is_not_runtime_candidate(self) -> None:
        candidate = self._candidate(dirty=True)
        record = self.coordinator.runtime_candidate_record(candidate, evidence_closure_sha="6" * 40)
        self.assertIsNone(record["candidateCommitSha"])
        self.assertEqual(record["evidenceOnlyClosureSha"], "6" * 40)
        self.assertNotEqual(record["evidenceOnlyClosureSha"], record["baseCommitSha"])

    def test_46_native_worktree_feature_is_enabled_explicitly(self) -> None:
        native = importlib.import_module("runtime.workflow.native")
        executable = self.root / "codex.exe"
        executable.write_bytes(b"fixture")
        command = native.build_exec_command(executable, "run the workflow")
        self.assertEqual(
            command[1:7],
            ["exec", "--enable", "worktrees", "--worktree", "--approve-for-me", "--json"],
        )

    def test_47_append_refuses_a_changed_on_disk_prefix(self) -> None:
        stale = self.ledger_module.WorkflowLedger(self.ledger.path)
        self.ledger.append_raw({"source": "first writer"})
        with self.assertRaises(self.ledger_module.LedgerError):
            stale.append_raw({"source": "stale writer"})

    def test_48_coordinator_can_rehydrate_exact_accepted_state(self) -> None:
        subject = self._to_green()
        loaded = self.coordinator_module.WorkflowCoordinator.load(self.ledger)
        self.assertEqual(loaded.state, self.model.WorkflowState.GREEN_CONFIRMED)
        self.assertEqual(loaded.current_candidate, subject)
        self.assertEqual(loaded.green_candidate, subject)

    def test_49_rehydration_rejects_a_cross_workflow_ledger(self) -> None:
        foreign = self.coordinator_module.WorkflowCoordinator.create(
            ledger=self.ledger,
            workflow_id="workflow-2",
            attempt_id="attempt-2",
            task_digest=SHA256,
            base_commit_sha=SHA40,
            cek_sha="c" * 40,
            runtime_identity={"version": "0.155.1", "binarySha256": "d" * 64},
        )
        self.assertIsNotNone(foreign)
        with self.assertRaises(self.coordinator_module.TransitionError):
            self.coordinator_module.WorkflowCoordinator.load(self.ledger)

    def test_50_public_export_pseudonymizes_parent_and_child_identities(self) -> None:
        self.ledger.append_raw({
            "parentIdentity": "private-parent-session",
            "childIdentity": "private-child-session",
            "startChildIdentity": "private-child-session",
            "stopChildIdentity": "private-child-session",
        })
        exported = json.dumps(self.ledger.sanitized_export(), sort_keys=True)
        self.assertNotIn("private-parent-session", exported)
        self.assertNotIn("private-child-session", exported)
        evidence = self.ledger.sanitized_export()["events"][-1]["evidence"]
        self.assertNotEqual(evidence["parentIdentity"], evidence["childIdentity"])
        self.assertEqual(evidence["childIdentity"], evidence["startChildIdentity"])
        self.assertEqual(evidence["childIdentity"], evidence["stopChildIdentity"])


if __name__ == "__main__":
    unittest.main()
