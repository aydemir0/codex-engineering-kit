from __future__ import annotations

import hashlib
import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "release_contracts" / "assets.json"
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
ORCHESTRATOR = ROOT / "skills" / "orchestrator" / "SKILL.md"
README = ROOT / "README.md"
ARCHITECTURE = ROOT / "docs" / "architecture.md"
CONTRIBUTING = ROOT / "CONTRIBUTING.md"
CLAIMS = ROOT / "release_contracts" / "claims.json"
CI = ROOT / ".github" / "workflows" / "ci.yml"
INSTALLER = ROOT / "scripts" / "install.ps1"

KINDS = {
    "plugin-native-skill",
    "project-local-native-agent",
    "parent-context-role-contract",
}


def discovered_paths() -> dict[str, set[str]]:
    return {
        "plugin-native-skill": {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "skills").glob("*/SKILL.md")
        },
        "project-local-native-agent": {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / ".codex" / "agents").glob("*.toml")
        },
        "parent-context-role-contract": {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "skills" / "orchestrator" / "references" / "roles").glob("*.md")
        },
    }


class AssetStocktakeContractTests(unittest.TestCase):
    def load_inventory(self) -> dict:
        self.assertTrue(INVENTORY.is_file(), "missing release_contracts/assets.json")
        return json.loads(INVENTORY.read_text(encoding="utf-8"))

    def records(self) -> list[dict]:
        records = self.load_inventory().get("assets")
        self.assertIsInstance(records, list)
        return records

    def test_inventory_covers_each_discovered_asset_exactly_once(self) -> None:
        expected = discovered_paths()
        actual = {kind: set() for kind in KINDS}
        seen_ids: set[str] = set()
        seen_paths: set[str] = set()

        for record in self.records():
            self.assertIn(record.get("kind"), KINDS)
            self.assertNotIn(record.get("id"), seen_ids)
            self.assertNotIn(record.get("path"), seen_paths)
            seen_ids.add(record["id"])
            seen_paths.add(record["path"])
            actual[record["kind"]].add(record["path"])

        self.assertEqual(actual, expected)

    def test_every_record_has_a_reviewable_contract(self) -> None:
        required = (
            "id",
            "name",
            "kind",
            "path",
            "purpose",
            "activation",
            "outputContract",
            "mutation",
            "overlap",
            "runtimeSupport",
        )
        for record in self.records():
            with self.subTest(asset=record.get("id")):
                for key in required:
                    self.assertIsInstance(record.get(key), str)
                    self.assertTrue(record[key].strip(), f"empty {key}")
                self.assertTrue((ROOT / record["path"]).is_file())

    def test_names_and_skill_interface_metadata_match_real_assets(self) -> None:
        records = self.records()
        metadata_paths: set[str] = set()
        for record in records:
            path = ROOT / record["path"]
            if record["kind"] == "plugin-native-skill":
                match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", path.read_text(encoding="utf-8"))
                self.assertIsNotNone(match)
                self.assertEqual(record["name"], path.parent.name)
                self.assertEqual(match.group(1), record["name"])
                metadata = record.get("interfaceMetadata")
                self.assertIsInstance(metadata, str)
                self.assertTrue((ROOT / metadata).is_file())
                metadata_paths.add(metadata)
            elif record["kind"] == "project-local-native-agent":
                data = tomllib.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(record["name"], path.stem)
                self.assertEqual(data.get("name"), record["name"])
            else:
                self.assertEqual(record["name"], path.stem)

        expected_metadata = {
            path.relative_to(ROOT).as_posix()
            for path in (ROOT / "skills").glob("*/agents/openai.yaml")
        }
        self.assertEqual(metadata_paths, expected_metadata)
        self.assertTrue(metadata_paths.isdisjoint({record["path"] for record in records}))

    def test_primary_assets_have_no_exact_content_duplicates(self) -> None:
        by_digest: dict[str, list[str]] = {}
        for paths in discovered_paths().values():
            for relative in paths:
                digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
                by_digest.setdefault(digest, []).append(relative)
        duplicates = [paths for paths in by_digest.values() if len(paths) > 1]
        self.assertEqual(duplicates, [])

    def test_orchestrator_routes_every_reference_role_without_phantoms(self) -> None:
        text = ORCHESTRATOR.read_text(encoding="utf-8")
        table = text.split("## Routing table", 1)[1].split("## Intent keywords", 1)[0]
        routed = set(re.findall(r"`([a-z][a-z0-9-]+)`", table))
        roles = {Path(path).stem for path in discovered_paths()["parent-context-role-contract"]}
        self.assertEqual(routed, roles)

    def test_cross_class_relationships_are_explicit_and_resolve(self) -> None:
        data = self.load_inventory()
        roles = {Path(path).stem for path in discovered_paths()["parent-context-role-contract"]}
        agents = {Path(path).stem for path in discovered_paths()["project-local-native-agent"]}
        relationships = data.get("relationships")
        self.assertIsInstance(relationships, list)
        pairs = {(item["referenceRole"], item["nativeAgent"]) for item in relationships}
        self.assertEqual(
            pairs,
            {
                ("architect", "architect"),
                ("build-error-resolver", "build-resolver"),
                ("code-reviewer", "reviewer"),
                ("e2e-runner", "e2e-runner"),
                ("refactor-cleaner", "refactor-cleaner"),
                ("security-reviewer", "security-reviewer"),
            },
        )
        for relationship in relationships:
            self.assertIn(relationship["referenceRole"], roles)
            self.assertIn(relationship["nativeAgent"], agents)
            self.assertTrue(relationship.get("boundary", "").strip())
        self.assertEqual(
            set(data.get("parentOnlyRoles", [])),
            {"doc-updater", "planner", "tdd-guide"},
        )
        self.assertEqual(
            set(data.get("agentOnlyDefinitions", [])),
            {"docs-researcher", "explorer"},
        )

    def test_cli_0153_support_boundary_is_explicit_per_asset_class(self) -> None:
        data = self.load_inventory()
        boundary = data.get("supportBoundary", {})
        self.assertEqual(boundary.get("runtime"), "Codex CLI 0.153.0")
        self.assertEqual(boundary.get("pluginNativeSkills"), "supported")
        self.assertEqual(boundary.get("projectLocalNativeAgents"), "supported")
        self.assertEqual(boundary.get("pluginNativeCustomAgents"), "unsupported-deferred")
        self.assertIn("does not register custom agent roles", boundary.get("limitation", ""))

        by_kind = {kind: [] for kind in KINDS}
        for record in self.records():
            by_kind[record["kind"]].append(record)
        self.assertTrue(all(item["runtimeSupport"] == "plugin-native" for item in by_kind["plugin-native-skill"]))
        self.assertTrue(all(item["runtimeSupport"] == "parent-context-only" for item in by_kind["parent-context-role-contract"]))

        agent_support = {item["name"]: item["runtimeSupport"] for item in by_kind["project-local-native-agent"]}
        self.assertEqual(agent_support["reviewer"], "verified-project-local-cli-0.153")
        self.assertEqual(agent_support["explorer"], "verified-project-local-cli-0.153")
        for name in set(agent_support) - {"reviewer", "explorer"}:
            self.assertEqual(agent_support[name], "contract-only-project-local")

        plugin = json.loads(PLUGIN.read_text(encoding="utf-8"))
        self.assertEqual(plugin.get("skills"), "./skills/")
        self.assertNotIn("agents", plugin)

    def test_truth_docs_use_derived_counts_and_runtime_boundaries(self) -> None:
        paths = discovered_paths()
        expected = (
            f"{len(paths['plugin-native-skill'])} plugin-native skills",
            f"{len(paths['project-local-native-agent'])} project-local native agent definitions",
            f"{len(paths['parent-context-role-contract'])} parent-context role contracts",
        )
        for document in (README, ARCHITECTURE):
            text = document.read_text(encoding="utf-8")
            with self.subTest(document=document.name):
                for phrase in expected:
                    self.assertIn(phrase, text)
                self.assertIn(
                    "Plugin installation does not register custom agent roles on Codex CLI 0.153.0.",
                    text,
                )
                self.assertIn(
                    "Skill `agents/openai.yaml` files are interface metadata, not agent definitions.",
                    text,
                )

    def test_release_claims_do_not_generalize_agent_runtime_evidence(self) -> None:
        claims = {item["id"]: item for item in json.loads(CLAIMS.read_text(encoding="utf-8"))["claims"]}
        skill_wording = claims["skills-eight"]["publicWording"]
        self.assertIn("plugin-native", skill_wording)
        agent_wording = claims["native-subagents"]["publicWording"]
        self.assertIn("reviewer", agent_wording)
        self.assertIn("explorer", agent_wording)
        self.assertIn("does not register custom agent roles", agent_wording)

    def test_contribution_policy_has_no_stale_count_and_requires_admission_evidence(self) -> None:
        text = CONTRIBUTING.read_text(encoding="utf-8")
        self.assertNotIn("v0.1 intentionally exposes exactly six active skills", text)
        for phrase in (
            "workflow gap",
            "activation boundary",
            "overlap analysis",
            "context-cost rationale",
            "tests/eval story",
            "maintenance owner",
            "public evidence impact",
            "maintainer-local",
        ):
            self.assertIn(phrase, text)

    def test_ci_runs_asset_stocktake_contract(self) -> None:
        self.assertIn(
            "python -m unittest tests.test_asset_stocktake -v",
            CI.read_text(encoding="utf-8"),
        )

    def test_powershell_installer_subset_is_explicit(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        block = text.split("$SkillNames = @(", 1)[1].split(")", 1)[0]
        installed = set(re.findall(r"'([a-z][a-z0-9-]+)'", block))
        data = self.load_inventory()
        delivery = data.get("delivery", {})
        self.assertEqual(set(delivery.get("powerShellInstallerSkills", [])), installed)
        all_skills = {
            record["name"]
            for record in self.records()
            if record["kind"] == "plugin-native-skill"
        }
        self.assertEqual(
            set(delivery.get("pluginOnlySkills", [])),
            all_skills - installed,
        )
        self.assertIn(
            "The PowerShell installer owns six core skills; the optional domain packs are plugin-only.",
            README.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
