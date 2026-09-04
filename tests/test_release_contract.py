from pathlib import Path
import re
import unittest

from release_contracts.model import (
    ClaimRecord,
    CompatibilityRecord,
    CompatibilityResult,
    load_claims,
    load_compatibility,
    validate_release_data,
)

ROOT = Path(__file__).resolve().parents[1]
CLAIMS = ROOT / "release_contracts" / "claims.json"
COMPAT = ROOT / "release_contracts" / "compatibility.json"


class ReleaseModelTests(unittest.TestCase):
    def test_release_data_loads_and_validates(self) -> None:
        claims = load_claims(CLAIMS)
        compatibility = load_compatibility(COMPAT)
        self.assertGreaterEqual(len(claims), 11)
        self.assertGreaterEqual(len(compatibility), 12)
        self.assertEqual(validate_release_data(claims, compatibility), ())

    def test_pass_compatibility_requires_evidence(self) -> None:
        record = CompatibilityRecord(
            surface="explicit-hooks",
            cli_0147=CompatibilityResult("PASS", (), ""),
            desktop_0152=CompatibilityResult("NOT_RUN", (), "not run"),
        )
        errors = validate_release_data((), (record,))
        self.assertTrue(any("PASS requires evidence" in error for error in errors))

    def test_verified_claim_requires_runtime_evidence(self) -> None:
        claim = ClaimRecord(
            id="native-hooks-default",
            wording="Native plugin hooks",
            state="VERIFIED",
            implementation_evidence=("tests/test_hook_contract.py",),
            runtime_evidence=(),
            runtime_scope="Codex CLI 0.147.0",
            limitation="",
            public_wording="Native plugin hooks are verified on Codex CLI 0.147.0.",
        )
        errors = validate_release_data((claim,), ())
        self.assertTrue(any("VERIFIED requires runtime evidence" in error for error in errors))

    def test_duplicate_claim_ids_are_rejected(self) -> None:
        first = ClaimRecord("same", "a", "LIMITED", ("x",), (), "", "limited", "a")
        second = ClaimRecord("same", "b", "LIMITED", ("y",), (), "", "limited", "b")
        errors = validate_release_data((first, second), ())
        self.assertTrue(any("duplicate claim id" in error for error in errors))

    def test_absolute_evidence_paths_are_rejected(self) -> None:
        claim = ClaimRecord(
            id="bad-path",
            wording="Bad path",
            state="IMPLEMENTED",
            implementation_evidence=("C:/Users/name/private.md",),
            runtime_evidence=(),
            runtime_scope="",
            limitation="",
            public_wording="Bad path",
        )
        errors = validate_release_data((claim,), ())
        self.assertTrue(any("repository-relative" in error for error in errors))


class ReleaseDocumentationTests(unittest.TestCase):
    def test_release_documents_name_both_baselines(self) -> None:
        compatibility = (ROOT / "docs" / "release" / "compatibility-matrix.md").read_text(encoding="utf-8")
        claims = (ROOT / "docs" / "release" / "claim-evidence-matrix.md").read_text(encoding="utf-8")
        for text in (compatibility, claims):
            self.assertIn("0.147.0", text)
            self.assertIn("0.152.0", text)

    def test_compatibility_document_contains_every_surface(self) -> None:
        text = (ROOT / "docs" / "release" / "compatibility-matrix.md").read_text(encoding="utf-8")
        for record in load_compatibility(COMPAT):
            self.assertIn(record.surface, text)

    def test_claim_document_contains_every_claim(self) -> None:
        text = (ROOT / "docs" / "release" / "claim-evidence-matrix.md").read_text(encoding="utf-8")
        for record in load_claims(CLAIMS):
            self.assertIn(record.id, text)

    def test_plan_f_release_markdown_is_sanitized(self) -> None:
        paths = [
            ROOT / "docs" / "release" / "compatibility-matrix.md",
            ROOT / "docs" / "release" / "claim-evidence-matrix.md",
            ROOT / "docs" / "research" / "evidence" / "codex-cli-0.147.0-plan-f-compatibility.md",
            ROOT / "docs" / "research" / "evidence" / "codex-desktop-0.152.0-plan-f-compatibility.md",
        ]
        text = "\n".join(path.read_text(encoding="utf-8") for path in paths)
        self.assertNotRegex(text, re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,})\b"))
        self.assertNotRegex(text, re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE))
        self.assertNotIn("/Users/", text)
        self.assertNotIn("/home/", text)
        self.assertNotIn("sessionId", text)


if __name__ == "__main__":
    unittest.main()
