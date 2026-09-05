from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE = ROOT / "docs" / "architecture.md"
README = ROOT / "README.md"
ROADMAP = ROOT / "ROADMAP.md"
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
CI = ROOT / ".github" / "workflows" / "ci.yml"


def shipped_skills() -> tuple[str, ...]:
    names = []
    for path in (ROOT / "skills").iterdir():
        if path.is_dir() and (path / "SKILL.md").is_file():
            names.append(path.name)
    return tuple(sorted(names))


def native_agents() -> tuple[str, ...]:
    return tuple(sorted(path.stem for path in (ROOT / ".codex" / "agents").glob("*.toml")))


class ArchitectureTruthContractTests(unittest.TestCase):
    def test_architecture_names_every_shipped_skill(self) -> None:
        text = ARCHITECTURE.read_text(encoding="utf-8")
        skills = shipped_skills()
        self.assertTrue(skills)
        for skill in skills:
            self.assertIn(f"`{skill}`", text)
        self.assertIn(f"{len(skills)} shipped skills", text)

    def test_architecture_names_every_native_agent(self) -> None:
        text = ARCHITECTURE.read_text(encoding="utf-8")
        agents = native_agents()
        self.assertTrue(agents)
        for agent in agents:
            self.assertIn(f"`{agent}`", text)
        self.assertIn(f"{len(agents)} native subagents", text)

    def test_architecture_removes_legacy_v01_primary_lifecycle(self) -> None:
        text = ARCHITECTURE.read_text(encoding="utf-8")
        self.assertNotIn("v0.1 deliberately registers only six active skills", text)
        self.assertNotIn("scripts/codex-wrapper.ps1\n  preflight", text)
        for required in (
            ".codex-plugin/plugin.json",
            ".codex/agents/",
            "hooks/hooks.json",
            "runtime/",
            "release_contracts/",
        ):
            self.assertIn(required, text)

    def test_architecture_separates_current_baseline_from_v1_target(self) -> None:
        text = ARCHITECTURE.read_text(encoding="utf-8")
        self.assertIn("## Current implemented baseline", text)
        self.assertIn("## v1.0 target architecture", text)
        target = text.split("## v1.0 target architecture", 1)[1]
        self.assertIn("target", target.casefold())
        self.assertIn("not a claim that every target layer is already release-ready", target.casefold())

    def test_public_identity_uses_evidence_bound_positioning(self) -> None:
        plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
        readme = README.read_text(encoding="utf-8")
        architecture = ARCHITECTURE.read_text(encoding="utf-8")
        self.assertEqual(plugin["name"], "codex-engineering-kit")
        for text in (readme, architecture):
            self.assertIn("Codex Engineering Kit", text)
            self.assertIn("Evidence-bound engineering workflows for OpenAI Codex", text)
            self.assertIn("independent", text.casefold())

    def test_roadmap_links_v1_design_and_master_plan(self) -> None:
        text = ROADMAP.read_text(encoding="utf-8")
        self.assertIn(
            "docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md",
            text,
        )
        self.assertIn(
            "docs/superpowers/plans/2026-09-05-v1-openai-ready-master.md",
            text,
        )

    def test_ci_runs_architecture_contract(self) -> None:
        text = CI.read_text(encoding="utf-8")
        content = text.split("  content-contracts:", 1)[1].split("\n  powershell-contracts:", 1)[0]
        self.assertIn("python -m unittest tests.test_architecture_contract -v", content)


if __name__ == "__main__":
    unittest.main()
