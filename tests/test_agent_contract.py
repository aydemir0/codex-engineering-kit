from __future__ import annotations

import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS_DIR = ROOT / ".codex" / "agents"
REVIEWER = AGENTS_DIR / "reviewer.toml"
PROJECT_CONFIG = ROOT / ".codex" / "config.toml"
CONTROLLED_WRITE_AGENTS = {
    "build-resolver",
    "e2e-runner",
    "refactor-cleaner",
}


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

    def test_project_agent_concurrency_is_bounded_to_four(self) -> None:
        data = self.load_toml(PROJECT_CONFIG)
        agents = data.get("agents")
        self.assertIsInstance(agents, dict)
        self.assertEqual(agents.get("max_concurrent_threads_per_session"), 4)

    def test_controlled_write_agents_have_portable_identity_fields(self) -> None:
        for name in CONTROLLED_WRITE_AGENTS:
            with self.subTest(agent=name):
                path = AGENTS_DIR / f"{name}.toml"
                data = self.load_toml(path)
                self.assertEqual(data.get("name"), name)
                self.assertTrue(data.get("description", "").strip())
                self.assertTrue(data.get("developer_instructions", "").strip())
                self.assertLessEqual(len(data["description"]), 240)
                self.assertLessEqual(len(data["developer_instructions"]), 4000)

    def test_controlled_write_agents_inherit_parent_model_and_reasoning(self) -> None:
        for name in CONTROLLED_WRITE_AGENTS:
            with self.subTest(agent=name):
                data = self.load_toml(AGENTS_DIR / f"{name}.toml")
                for key in (
                    "model",
                    "model_provider",
                    "model_reasoning_effort",
                    "service_tier",
                ):
                    self.assertNotIn(key, data)

    def test_controlled_write_agents_require_isolated_worktree_and_conflict_stop(self) -> None:
        for name in CONTROLLED_WRITE_AGENTS:
            with self.subTest(agent=name):
                data = self.load_toml(AGENTS_DIR / f"{name}.toml")
                instructions = data["developer_instructions"].casefold()
                self.assertIn("isolated worktree", instructions)
                self.assertIn("one write agent", instructions)
                self.assertIn("stop on conflict", instructions)
                self.assertIn("do not merge", instructions)
                self.assertIn("verification", instructions)

    def test_agent_files_have_no_placeholders_or_machine_paths(self) -> None:
        paths = [REVIEWER] + [
            AGENTS_DIR / f"{name}.toml" for name in CONTROLLED_WRITE_AGENTS
        ]
        for path in paths:
            with self.subTest(path=path.name):
                text = path.read_text(encoding="utf-8") if path.exists() else ""
                self.assertNotRegex(text, r"\b(?:TODO|TBD)\b")
                self.assertNotIn("C:\\Users\\", text)
                self.assertNotIn("/Users/", text)
                self.assertNotIn("/home/", text)


if __name__ == "__main__":
    unittest.main()
