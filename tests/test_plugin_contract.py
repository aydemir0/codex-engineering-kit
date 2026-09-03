from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
MARKETPLACE = ROOT / ".agents" / "plugins" / "marketplace.json"


class PluginContractTests(unittest.TestCase):
    def load_json(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_manifest_identity_and_version(self) -> None:
        data = self.load_json(PLUGIN)
        self.assertEqual(data["name"], "codex-engineering-kit")
        self.assertRegex(data["version"], r"^0\.2\.0-alpha\.1$")
        self.assertTrue(data["description"].strip())
        self.assertEqual(data["license"], "MIT")
        self.assertEqual(data["skills"], "./skills/")

    def test_manifest_keeps_open_risk_out_of_primary_path(self) -> None:
        data = self.load_json(PLUGIN)
        self.assertNotIn("hooks", data)
        self.assertNotIn("mcpServers", data)
        self.assertNotIn("apps", data)

    def test_manifest_has_real_publisher_metadata(self) -> None:
        data = self.load_json(PLUGIN)
        self.assertEqual(data["author"]["name"], "aydemir0")
        self.assertEqual(
            data["repository"],
            "https://github.com/aydemir0/codex-engineering-kit",
        )
        self.assertEqual(
            data["homepage"],
            "https://github.com/aydemir0/codex-engineering-kit",
        )
        interface = data["interface"]
        self.assertEqual(interface["displayName"], "Codex Engineering Kit")
        self.assertEqual(interface["developerName"], "aydemir0")
        prompts = interface.get("defaultPrompt", [])
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(all(len(prompt) <= 128 for prompt in prompts))

    def test_marketplace_points_to_local_plugin(self) -> None:
        data = self.load_json(MARKETPLACE)
        plugins = data["plugins"]
        self.assertEqual(len(plugins), 1)
        entry = plugins[0]
        self.assertEqual(entry["name"], "codex-engineering-kit")
        self.assertEqual(entry["source"]["source"], "local")
        # Codex resolves local marketplace plugin paths from the marketplace
        # repository root, not from the nested .agents/plugins directory.
        self.assertEqual(entry["source"]["path"], ".")
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_USE")

    def test_no_placeholders_or_machine_paths(self) -> None:
        plugin_text = PLUGIN.read_text(encoding="utf-8") if PLUGIN.exists() else ""
        marketplace_text = (
            MARKETPLACE.read_text(encoding="utf-8") if MARKETPLACE.exists() else ""
        )
        text = plugin_text + marketplace_text
        self.assertNotRegex(text, r"\b(?:TODO|TBD)\b")
        self.assertNotIn("C:\\Users\\", text)
        self.assertNotIn("/Users/", text)
        self.assertNotIn("\\.cache\\", text)


if __name__ == "__main__":
    unittest.main()
