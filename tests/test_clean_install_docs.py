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


if __name__ == "__main__":
    unittest.main()
