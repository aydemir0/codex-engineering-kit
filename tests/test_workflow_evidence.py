from __future__ import annotations

import copy
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

REQUIRED_STAGES = (
    "classify",
    "plan",
    "red",
    "implement",
    "green",
    "review",
    "verify",
)

try:
    from scripts.acceptance.workflow_evidence import main, validate_workflow_record
except ModuleNotFoundError:
    main = None
    validate_workflow_record = None


def valid_record() -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "repositoryCommit": "0123456789abcdef0123456789abcdef01234567",
        "runtimeVersion": "codex-cli 0.153.0",
        "fixture": "representative-workflow-v1",
        "stages": [
            {
                "name": name,
                "result": "PASS",
                "evidence": [f"evidence/{name}.txt"],
            }
            for name in REQUIRED_STAGES
        ],
        "result": "PASS",
    }


class WorkflowEvidenceContractTests(unittest.TestCase):
    def validate(self, record: dict[str, object]) -> tuple[str, ...]:
        self.assertIsNotNone(
            validate_workflow_record,
            "workflow evidence validator is not implemented",
        )
        return validate_workflow_record(record)

    def test_valid_record_has_no_errors(self) -> None:
        self.assertEqual(self.validate(valid_record()), ())

    def test_missing_required_stage_is_rejected(self) -> None:
        record = valid_record()
        record["stages"] = [
            stage
            for stage in record["stages"]
            if stage["name"] != "review"
        ]

        errors = self.validate(record)

        self.assertTrue(errors)

    def test_duplicate_stage_is_rejected(self) -> None:
        record = valid_record()
        record["stages"].append(copy.deepcopy(record["stages"][0]))

        errors = self.validate(record)

        self.assertTrue(errors)

    def test_non_40_hex_repository_sha_is_rejected(self) -> None:
        record = valid_record()
        record["repositoryCommit"] = "bad-sha"

        errors = self.validate(record)

        self.assertTrue(errors)

    def test_pass_stage_without_evidence_is_rejected(self) -> None:
        record = valid_record()
        record["stages"][0]["evidence"] = []

        errors = self.validate(record)

        self.assertTrue(errors)

    def test_empty_runtime_version_is_rejected(self) -> None:
        record = valid_record()
        record["runtimeVersion"] = ""

        errors = self.validate(record)

        self.assertTrue(errors)

    def test_wrong_fixture_name_is_rejected(self) -> None:
        record = valid_record()
        record["fixture"] = "something-else"

        errors = self.validate(record)

        self.assertTrue(errors)

    def test_sensitive_or_machine_local_evidence_is_rejected(self) -> None:
        forbidden = (
            r"C:\Users\alice\workflow.json",
            "/Users/alice/workflow.json",
            "/home/alice/workflow.json",
            "sessionId=private-session",
            "ghp_" + ("A" * 24),
            "sk-" + ("B" * 24),
        )

        for value in forbidden:
            with self.subTest(value=value):
                record = valid_record()
                record["stages"][0]["evidence"] = [value]

                errors = self.validate(record)

                self.assertTrue(
                    errors,
                    f"expected sensitive evidence to be rejected: {value}",
                )



    def test_cli_valid_record_returns_zero_without_echoing_evidence(self) -> None:
        self.assertIsNotNone(
            main,
            "workflow evidence CLI is not implemented",
        )

        with tempfile.TemporaryDirectory() as tmp:
            record_path = Path(tmp) / "record.json"
            record_path.write_text(
                json.dumps(valid_record()),
                encoding="utf-8",
            )

            stdout = StringIO()

            with redirect_stdout(stdout):
                code = main([
                    "validate",
                    "--record",
                    str(record_path),
                ])

        output = stdout.getvalue()

        self.assertEqual(code, 0)
        self.assertIn("PASS", output)
        self.assertNotIn("evidence/classify.txt", output)

if __name__ == "__main__":
    unittest.main()
