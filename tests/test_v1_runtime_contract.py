from pathlib import Path
import json
import unittest

from release_contracts.model import load_claims, load_compatibility

ROOT = Path(__file__).resolve().parents[1]
COMPAT = ROOT / "release_contracts" / "compatibility.json"
CLAIMS = ROOT / "release_contracts" / "claims.json"

COMPAT_DOC = ROOT / "docs" / "release" / "compatibility-matrix.md"
CLAIM_DOC = ROOT / "docs" / "release" / "claim-evidence-matrix.md"

CLI_0153_EVIDENCE = (
    "docs/research/evidence/codex-cli-0.153.0-v1-runtime-closure.md"
)
WS7_EVIDENCE = "docs/research/evidence/codex-v1-ws7-clean-install.md"


class V1RuntimeCompatibilityContractTests(unittest.TestCase):
    def test_v1_contract_exposes_cli_0153_baseline(self) -> None:
        records = load_compatibility(COMPAT)

        self.assertGreater(len(records), 0)

        for record in records:
            self.assertTrue(
                hasattr(record, "cli_0153"),
                f"{record.surface} does not expose cli_0153",
            )
            self.assertIsNotNone(
                record.cli_0153,
                f"{record.surface} has no cli_0153 result",
            )

    def test_json_contains_cli0153_for_every_surface(self) -> None:
        payload = json.loads(COMPAT.read_text(encoding="utf-8"))

        for row in payload["compatibility"]:
            self.assertIn(
                "cli0153",
                row,
                f"{row['surface']} is missing cli0153",
            )

    def test_cli_0153_surface_classifications_match_fresh_campaign(self) -> None:
        expected = {
            "plugin-discovery": "PASS",
            "marketplace-install-list": "PASS",
            "skill-discovery": "NOT_RUN",
            "default-hooks": "PASS",
            "explicit-hooks": "PASS",
            "hook-lifecycle": "PASS",
            "pretool-deny-allow": "PASS",
            "native-subagent": "PASS",
            "compaction-state": "PASS",
            "session-end": "PASS",
            "interactive-plugin-discovery": "NOT_RUN",
            "managed-install-lifecycle": "PASS",
            "desktop-parent-wait": "NOT_RUN",
        }

        records = {
            record.surface: record
            for record in load_compatibility(COMPAT)
        }

        self.assertEqual(set(records), set(expected))

        for surface, expected_status in expected.items():
            result = records[surface].cli_0153
            self.assertIsNotNone(result)

            assert result is not None

            self.assertEqual(
                result.status,
                expected_status,
                f"{surface}/cli0153 has wrong classification",
            )

            if expected_status == "PASS":
                required_evidence = WS7_EVIDENCE if surface == "managed-install-lifecycle" else CLI_0153_EVIDENCE
                self.assertIn(
                    required_evidence,
                    result.evidence,
                    f"{surface}/cli0153 lacks fresh evidence",
                )

    def test_cli_0153_pass_evidence_is_committed_and_repository_relative(self) -> None:
        records = load_compatibility(COMPAT)

        for record in records:
            result = record.cli_0153
            self.assertIsNotNone(result)

            assert result is not None

            if result.status != "PASS":
                continue

            self.assertGreater(
                len(result.evidence),
                0,
                f"{record.surface}/cli0153 PASS has no evidence",
            )

            for evidence in result.evidence:
                path = Path(evidence)
                self.assertFalse(path.is_absolute())
                self.assertTrue(
                    (ROOT / path).is_file(),
                    f"missing evidence file: {evidence}",
                )

    def test_runtime_claims_project_fresh_cli_0153_evidence(self) -> None:
        claims = {
            claim.id: claim
            for claim in load_claims(CLAIMS)
        }

        runtime_claims = (
            "plugin-packaging",
            "native-hooks-default",
            "native-subagents",
            "state-compaction",
            "compatibility-window",
        )

        for claim_id in runtime_claims:
            claim = claims[claim_id]

            self.assertIn(
                "0.153.0",
                claim.runtime_scope,
                f"{claim_id} runtimeScope omits CLI 0.153.0",
            )

            self.assertIn(
                CLI_0153_EVIDENCE,
                claim.runtime_evidence,
                f"{claim_id} lacks fresh CLI 0.153.0 evidence",
            )

        self.assertEqual(
            claims["native-hooks-default"].state,
            "VERIFIED",
            "default hooks should be VERIFIED at the scoped CLI 0.153.0 boundary",
        )

    def test_compatibility_window_keeps_runtime_boundaries_separate(self) -> None:
        claim = next(
            item
            for item in load_claims(CLAIMS)
            if item.id == "compatibility-window"
        )

        for version in ("0.147.0", "0.153.0", "0.152.0"):
            self.assertIn(version, claim.runtime_scope)
            self.assertIn(version, claim.public_wording)

        self.assertEqual(claim.state, "LIMITED")

    def test_release_docs_project_cli_0153_boundary(self) -> None:
        compatibility = COMPAT_DOC.read_text(encoding="utf-8")
        claims = CLAIM_DOC.read_text(encoding="utf-8")

        for text in (compatibility, claims):
            self.assertIn("0.147.0", text)
            self.assertIn("0.153.0", text)
            self.assertIn("0.152.0", text)
            self.assertIn(CLI_0153_EVIDENCE, text)

        self.assertIn("Codex CLI 0.153.0", compatibility)



    def test_release_docs_do_not_contain_encoding_replacement_question_marks(self) -> None:
        compatibility = COMPAT_DOC.read_text(encoding="utf-8")
        claims = CLAIM_DOC.read_text(encoding="utf-8")

        suspicious = []

        for name, document in (
            ("compatibility-matrix", compatibility),
            ("claim-evidence-matrix", claims),
        ):
            for number, line in enumerate(document.splitlines(), 1):
                if " ? " in line or line.rstrip().endswith("| ? |"):
                    suspicious.append(f"{name}:{number}:{line}")

        self.assertEqual(
            suspicious,
            [],
            "release docs contain PowerShell-encoding replacement question marks",
        )

    def test_compatibility_window_wording_names_fresh_cli_0153(self) -> None:
        claim = next(
            item
            for item in load_claims(CLAIMS)
            if item.id == "compatibility-window"
        )

        self.assertIn("0.147.0", claim.wording)
        self.assertIn("0.153.0", claim.wording)
        self.assertIn("0.152.0", claim.wording)


    def test_explicit_hooks_public_support_is_cli_0153_only(self) -> None:
        claims = {
            claim.id: claim
            for claim in load_claims(CLAIMS)
        }

        self.assertIn(
            "native-hooks-explicit",
            claims,
            "v1 requires a machine-readable scoped explicit-hooks claim",
        )

        claim = claims["native-hooks-explicit"]

        self.assertEqual(claim.state, "VERIFIED")
        self.assertEqual(
            claim.runtime_scope,
            "Codex CLI 0.153.0 only",
        )
        self.assertIn(CLI_0153_EVIDENCE, claim.runtime_evidence)

        wording = claim.public_wording
        self.assertIn("Codex CLI 0.153.0 only", wording)
        self.assertIn("0.147.0", wording)
        self.assertIn("0.152.0", wording)
        self.assertIn("not claimed", wording)

        records = {
            record.surface: record
            for record in load_compatibility(COMPAT)
        }
        explicit = records["explicit-hooks"]

        self.assertEqual(explicit.cli_0153.status, "PASS")
        self.assertEqual(explicit.cli_0147.status, "BLOCKED")
        self.assertEqual(explicit.desktop_0152.status, "BLOCKED")

    def test_risk_001_closes_only_at_scoped_v1_boundary(self) -> None:
        text = COMPAT_DOC.read_text(encoding="utf-8")

        start = text.index("### RISK-001")
        rest = text[start:]

        next_heading = rest.find("\n### ", 1)
        section = rest if next_heading == -1 else rest[:next_heading]

        self.assertIn("Status: CLOSED (v1 scoped)", section)
        self.assertIn("Codex CLI 0.153.0 only", section)
        self.assertIn("Codex CLI 0.147.0", section)
        self.assertIn("Codex Desktop 0.152.0", section)
        self.assertIn("not claimed", section)
        self.assertIn("does not convert", section)


    def test_explicit_hooks_claim_links_actual_fixture_provenance(self) -> None:
        claim = next(
            item
            for item in load_claims(CLAIMS)
            if item.id == "native-hooks-explicit"
        )

        required = {
            ".codex-plugin/plugin.json",
            "hooks/hooks.json",
            "scripts/acceptance/plugin_compatibility.py",
            "tests/test_plugin_compatibility.py",
        }

        self.assertTrue(
            required.issubset(set(claim.implementation_evidence)),
            "explicit-hooks claim must link the actual disposable-manifest implementation and test",
        )

        self.assertNotIn(
            "release_contracts/compatibility.json",
            claim.implementation_evidence,
            "compatibility output must not be used as circular implementation evidence",
        )

if __name__ == "__main__":
    unittest.main()
