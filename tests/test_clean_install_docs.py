from __future__ import annotations

import unittest
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class CleanInstallDocumentationTests(unittest.TestCase):
    def test_readme_documents_the_managed_lifecycle_and_truth_boundaries(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")

        for command in ("install", "verify", "update", "uninstall", "verify-clean"):
            self.assertIn(f"scripts/cek_lifecycle.py {command}", text)
        self.assertIn("Codex CLI 0.153.0", text)
        self.assertIn(".codex/agents/reviewer.toml", text)
        self.assertIn("project-local", text)
        self.assertIn("plugin-native custom agents", text.casefold())
        self.assertIn("unsupported/deferred", text.casefold())
        self.assertIn("eight plugin-native skills", text.casefold())
        self.assertIn("hooks/hooks.json", text)
        self.assertIn("six core skills", text.casefold())

    def test_readme_preserves_the_measured_ws6_boundary(self) -> None:
        texts = [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "benchmark.md").read_text(encoding="utf-8"),
        ]

        for text in texts:
            for wording in (
                "45 authenticated runs",
                "A 15/15 PASS",
                "B 15/15 PASS",
                "C 4/15 PASS",
                "34 PASS / 11 retained FAIL",
                "no retry or replacement",
                "unauthorized connector startup warning",
            ):
                self.assertIn(wording, text)
            self.assertNotIn("authenticated 45-run campaign has not been completed", text)

        claims = json.loads((ROOT / "release_contracts" / "claims.json").read_text(encoding="utf-8"))
        benchmark = next(item for item in claims["claims"] if item["id"] == "context-benchmark-protocol")
        self.assertEqual(benchmark["state"], "VERIFIED")
        self.assertIn("docs/research/evidence/codex-v1-ws6-benchmark.md", benchmark["runtimeEvidence"])
        self.assertIn("34 PASS / 11 retained FAIL", benchmark["publicWording"])

    def test_ws7_evidence_is_sanitized_and_reconciled(self) -> None:
        evidence = [
            (ROOT / "docs" / "research" / "evidence" / "codex-v1-ws7-clean-install.json").read_text(encoding="utf-8"),
            (ROOT / "docs" / "research" / "evidence" / "codex-v1-ws7-clean-install.md").read_text(encoding="utf-8"),
        ]
        for text in evidence:
            self.assertNotRegex(text, r"(?i)(auth\.json|bearer\s+[A-Za-z0-9._-]+|session[_ -]?id|thread[_ -]?id)")
            self.assertNotRegex(text, r"(?:[A-Za-z]:[\\/]|/Users/|/home/|C:\\\\Users\\\\)")
        payload = json.loads(evidence[0])
        self.assertTrue(payload["sanitized"])
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["sourceHead"], "0da70a7618592e26aeeba422d899f60dfe8a50e7")
        self.assertEqual(payload["candidateSha"], "4f4c7e130916b1370d86fd9fb3a4785d2c907c69")


if __name__ == "__main__":
    unittest.main()
