from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
