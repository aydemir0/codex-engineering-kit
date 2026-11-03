from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.cek_workflow import LifecycleError, _parser, _workflow_main


class M2BWorkflowCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.command = importlib.import_module("runtime.workflow.command")
        self.model = importlib.import_module("runtime.workflow.model")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.profile = self.root / "profile"
        self.normal = self.root / "normal"
        self.project = self.root / "project"
        self.normal.mkdir()
        self.project.mkdir()

    def test_parser_exposes_one_workflow_command_group(self) -> None:
        args = _parser().parse_args([
            "workflow",
            "status",
            "--workflow-root",
            str(self.profile),
            "--workflow-id",
            "workflow-1",
        ])
        self.assertEqual(args.action, "workflow")
        self.assertEqual(args.workflow_action, "status")

    def test_initialization_reaches_planned_with_structured_contracts(self) -> None:
        result = self.command.initialize_workflow(
            profile_root=self.profile,
            normal_codex_home=self.normal,
            project=self.project,
            workflow_id="workflow-1",
            task="Fix the fixture defect",
            cek_sha="a" * 40,
            base_commit_sha="b" * 40,
            runtime_identity={"version": "0.155.1", "binarySha256": "c" * 64},
            commands=("python -B -m unittest test_regression.py",),
            scope=("src/bug.py", "test_regression.py"),
        )
        self.assertEqual(result["state"], "PLANNED")
        self.assertTrue((self.profile / ".codex-kit" / "workflow-profile.json").is_file())
        self.assertTrue((self.profile / ".codex-kit" / "workflows" / "workflow-1" / "ledger.json").is_file())
        config = (self.profile / "config.toml").read_text(encoding="utf-8")
        self.assertIn('sandbox_mode = "workspace-write"', config)
        self.assertIn("network_access = false", config)
        self.assertIn(str(self.profile).replace("\\", "\\\\"), config)

    def test_stage_transition_rehydrates_and_appends(self) -> None:
        self.test_initialization_reaches_planned_with_structured_contracts()
        candidate = self.model.CandidateIdentity(
            "b" * 40,
            None,
            "d" * 40,
            "e" * 64,
            "f" * 64,
            "1" * 64,
            "worktree-1",
            "codex/worktree-1",
            True,
        )
        result = self.command.record_transition(
            self.profile,
            "workflow-1",
            self.model.WorkflowState.ISOLATION_READY,
            {"authorized": True, "worktreeId": "worktree-1", "candidate": candidate},
        )
        self.assertEqual(result["state"], "ISOLATION_READY")
        self.assertEqual(self.command.workflow_status(self.profile, "workflow-1")["eventCount"], 4)

    def test_status_does_not_expose_raw_session_or_secret_values(self) -> None:
        self.test_initialization_reaches_planned_with_structured_contracts()
        ledger = self.command.load_ledger(self.profile, "workflow-1")
        ledger.append_raw({"sessionId": "private-session", "message": "token=secret-value"})
        result = json.dumps(self.command.workflow_status(self.profile, "workflow-1"), sort_keys=True)
        self.assertNotIn("private-session", result)
        self.assertNotIn("secret-value", result)

    def test_resume_rejects_a_stale_candidate(self) -> None:
        self.test_stage_transition_rehydrates_and_appends()
        wrong = self.model.CandidateIdentity(
            "b" * 40,
            None,
            "d" * 40,
            "9" * 64,
            "f" * 64,
            "1" * 64,
            "worktree-1",
            "codex/worktree-1",
            True,
        )
        with self.assertRaises(self.command.StaleWorkflowError):
            self.command.resume_workflow(self.profile, "workflow-1", wrong, "worktree-1")

    def test_review_stage_rejects_parent_supplied_result_not_emitted_by_child(self) -> None:
        self.profile.mkdir()
        evidence = self.root / "review.json"
        evidence.write_text(
            json.dumps(
                {
                    "childIdentity": "child-1",
                    "resultSourceChildIdentity": "child-1",
                    "structuredResult": {
                        "disposition": "ACCEPT",
                        "role": "reviewer",
                        "findings": [],
                        "candidateManifestDigest": "9" * 64,
                        "candidateTreeOid": "8" * 40,
                    },
                }
            ),
            encoding="utf-8",
        )
        args = _parser().parse_args(
            [
                "workflow",
                "stage",
                "--workflow-root",
                str(self.profile),
                "--workflow-id",
                "workflow-1",
                "--target",
                "REVIEW_ACCEPTED",
                "--evidence",
                str(evidence),
            ]
        )
        observed = {
            "childIdentity": "child-1",
            "resultSourceChildIdentity": "child-1",
            "structuredResult": {
                "disposition": "ACCEPT",
                "role": "reviewer",
                "findings": [],
                "candidateManifestDigest": "7" * 64,
                "candidateTreeOid": "6" * 40,
            },
        }
        with patch("runtime.workflow.lifecycle.extract_reviewer_lifecycle", return_value=observed):
            with self.assertRaisesRegex(LifecycleError, "native child output"):
                _workflow_main(args)

    def test_lifecycle_output_can_stage_exact_review_without_model_added_fields(self) -> None:
        self.test_initialization_reaches_planned_with_structured_contracts()
        candidate = self.model.CandidateIdentity(
            "b" * 40,
            None,
            "d" * 40,
            "e" * 64,
            "f" * 64,
            "1" * 64,
            "worktree-1",
            "codex/worktree-1",
            True,
        )
        self.command.record_transition(
            self.profile,
            "workflow-1",
            self.model.WorkflowState.ISOLATION_READY,
            {"authorized": True, "worktreeId": "worktree-1", "candidate": candidate},
        )
        self.command.record_transition(self.profile, "workflow-1", self.model.WorkflowState.RED_REQUIRED, {})
        self.command.record_transition(
            self.profile,
            "workflow-1",
            self.model.WorkflowState.RED_CONFIRMED,
            {
                "result": "FAIL",
                "failureKind": "BEHAVIOR",
                "commandDigest": "f" * 64,
                "expectedSignature": "AssertionError",
                "candidate": candidate,
                "worktreeId": "worktree-1",
            },
        )
        self.command.record_transition(self.profile, "workflow-1", self.model.WorkflowState.IMPLEMENTING, {})
        self.command.record_transition(self.profile, "workflow-1", self.model.WorkflowState.GREEN_REQUIRED, {})
        self.command.record_transition(
            self.profile,
            "workflow-1",
            self.model.WorkflowState.GREEN_CONFIRMED,
            {"result": "PASS", "fresh": True, "commandDigest": "f" * 64, "candidate": candidate, "worktreeId": "worktree-1"},
        )
        self.command.record_transition(self.profile, "workflow-1", self.model.WorkflowState.REVIEW_REQUESTED, {})
        self.command.record_transition(
            self.profile,
            "workflow-1",
            self.model.WorkflowState.REVIEW_RUNNING,
            {"candidate": candidate, "parentIdentity": "parent-1", "reviewerAssetSha": "a" * 64},
        )
        native = {
            "source": "codex-native-session",
            "startEvent": "SubagentStart",
            "stopEvent": "SubagentStop",
            "parentIdentity": "parent-1",
            "startChildIdentity": "child-1",
            "stopChildIdentity": "child-1",
            "childIdentity": "child-1",
            "resultSourceChildIdentity": "child-1",
            "agentType": "reviewer",
            "structuredResult": {
                "disposition": "ACCEPT",
                "role": "reviewer",
                "findings": [],
                "candidateManifestDigest": candidate.candidate_manifest_digest,
                "candidateTreeOid": candidate.candidate_tree_oid,
            },
        }
        lifecycle_args = _parser().parse_args(
            ["workflow", "lifecycle", "--workflow-root", str(self.profile), "--workflow-id", "workflow-1"]
        )
        evidence_path = self.root / "native-review.json"
        with patch("runtime.workflow.lifecycle.extract_reviewer_lifecycle", return_value=native):
            evidence = _workflow_main(lifecycle_args)
            evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
            stage_args = _parser().parse_args(
                [
                    "workflow",
                    "stage",
                    "--workflow-root",
                    str(self.profile),
                    "--workflow-id",
                    "workflow-1",
                    "--target",
                    "REVIEW_ACCEPTED",
                    "--evidence",
                    str(evidence_path),
                ]
            )
            result = _workflow_main(stage_args)

        self.assertEqual(evidence["candidate"], candidate.to_payload())
        self.assertEqual(evidence["reviewerAssetSha"], "a" * 64)
        self.assertEqual(result["state"], "REVIEW_ACCEPTED")


if __name__ == "__main__":
    unittest.main()
