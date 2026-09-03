from __future__ import annotations

import unittest
from pathlib import Path

from scripts.acceptance.plugin_smoke import build_environment, find_plugin, sanitize_record


class PluginSmokeHelperTests(unittest.TestCase):
    def test_build_environment_replaces_existing_codex_home(self) -> None:
        base = {"CODEX_HOME": "C:/real-home", "KEEP_ME": "yes"}
        disposable = Path("C:/temp/cek-codex-home")

        result = build_environment(base, disposable)

        self.assertEqual(result["CODEX_HOME"], str(disposable))
        self.assertEqual(result["KEEP_ME"], "yes")
        self.assertEqual(base["CODEX_HOME"], "C:/real-home")

    def test_find_plugin_prefers_installed_result(self) -> None:
        payload = {
            "installed": [
                {
                    "name": "codex-engineering-kit",
                    "installed": True,
                    "enabled": True,
                }
            ],
            "available": [{"name": "codex-engineering-kit"}],
        }

        location, plugin = find_plugin(payload, "codex-engineering-kit")

        self.assertEqual(location, "installed")
        self.assertTrue(plugin["installed"])

    def test_find_plugin_finds_available_result(self) -> None:
        payload = {
            "installed": [],
            "available": [{"name": "codex-engineering-kit", "installed": False}],
        }

        location, plugin = find_plugin(payload, "codex-engineering-kit")

        self.assertEqual(location, "available")
        self.assertEqual(plugin["name"], "codex-engineering-kit")

    def test_find_plugin_raises_when_missing(self) -> None:
        with self.assertRaises(LookupError):
            find_plugin({"installed": [], "available": []}, "codex-engineering-kit")

    def test_sanitize_record_removes_local_paths_and_raw_streams(self) -> None:
        record = {
            "args": ["codex", "plugin", "add", "codex-engineering-kit@dev", "--json"],
            "returncode": 0,
            "stdout": '{"installedPath":"C:\\\\Users\\\\someone\\\\.codex\\\\plugins\\\\x"}',
            "stderr": "",
            "parsed": {
                "pluginId": "codex-engineering-kit@dev",
                "name": "codex-engineering-kit",
                "marketplaceName": "dev",
                "version": "0.2.0-alpha.1",
                "installedPath": "C:/Users/someone/.codex/plugins/x",
                "authPolicy": "ON_USE",
            },
        }

        result = sanitize_record(record)

        self.assertNotIn("stdout", result)
        self.assertNotIn("stderr", result)
        self.assertNotIn("installedPath", result["parsed"])
        self.assertEqual(result["parsed"]["name"], "codex-engineering-kit")
        self.assertEqual(result["returncode"], 0)


if __name__ == "__main__":
    unittest.main()
