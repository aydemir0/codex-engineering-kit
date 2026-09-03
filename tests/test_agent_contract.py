from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWER = ROOT / ".codex" / "agents" / "reviewer.toml"


class AgentContractTests(unittest.TestCase):
    def load_toml(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
        return tomllib.loads(path.read_text(encoding="utf-8"))

    def test_reviewer_has_portable_identity_fields(self) -> None:
        data = self.load_toml(REVIEWER)
        self.assertEqual(data["name"], "reviewer")
        self.assertTrue(data["description"].strip())
        self.assertTrue(data["developer_instructions"].strip())
        self.assertLessEqual(len(data["description"]), 240)
        self.assertLessEqual(len(data["developer_instructions"]), 4000)

    def test_reviewer_inherits_parent_model_and_reasoning(self) -> None:
        data = self.load_toml(REVIEWER)
        for key in (
            "model",
            "model_provider",
            "model_reasoning_effort",
            "service_tier",
        ):
            self.assertNotIn(key, data)

    def test_reviewer_is_explicitly_read_only_and_evidence_bound(self) -> None:
        data = self.load_toml(REVIEWER)
        instructions = data["developer_instructions"].casefold()
        self.assertIn("do not modify files", instructions)
        self.assertIn("do not create commits", instructions)
        self.assertIn("evidence", instructions)
        self.assertIn("findings", instructions)

    def test_reviewer_has_no_placeholders_or_machine_paths(self) -> None:
        text = REVIEWER.read_text(encoding="utf-8") if REVIEWER.exists() else ""
        self.assertNotRegex(text, r"\b(?:TODO|TBD)\b")
        self.assertNotIn("C:\\Users\\", text)
        self.assertNotIn("/Users/", text)


if __name__ == "__main__":
    unittest.main()
