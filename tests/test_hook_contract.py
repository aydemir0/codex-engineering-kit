from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOOKS_FILE = ROOT / "hooks" / "hooks.json"
DISPATCHER = ROOT / "hooks" / "scripts" / "hook_dispatch.py"
PLUGIN_MANIFEST = ROOT / ".codex-plugin" / "plugin.json"
GITIGNORE = ROOT / ".gitignore"

REQUIRED_EVENTS = {
    "SessionStart",
    "SessionEnd",
    "PreToolUse",
    "PostToolUse",
    "PreCompact",
    "PostCompact",
    "SubagentStart",
    "SubagentStop",
}


class NativeHookContractTests(unittest.TestCase):
    def load_json(self, path: Path) -> dict:
        self.assertTrue(path.is_file(), f"missing {path.relative_to(ROOT)}")
        return json.loads(path.read_text(encoding="utf-8"))

    def test_default_plugin_hook_file_declares_exact_required_events(self) -> None:
        data = self.load_json(HOOKS_FILE)
        hooks = data.get("hooks")
        self.assertIsInstance(hooks, dict)
        self.assertEqual(set(hooks), REQUIRED_EVENTS)

    def test_each_event_uses_portable_sync_command_dispatcher(self) -> None:
        hooks = self.load_json(HOOKS_FILE)["hooks"]
        unix_fragment = '$PLUGIN_ROOT/hooks/scripts/hook_dispatch.py'
        windows_fragment = r"%PLUGIN_ROOT%\hooks\scripts\hook_dispatch.py"

        for event in REQUIRED_EVENTS:
            with self.subTest(event=event):
                groups = hooks[event]
                self.assertIsInstance(groups, list)
                self.assertEqual(len(groups), 1)
                self.assertNotIn("matcher", groups[0])
                handlers = groups[0].get("hooks")
                self.assertIsInstance(handlers, list)
                self.assertEqual(len(handlers), 1)
                handler = handlers[0]
                self.assertEqual(handler.get("type"), "command")
                self.assertIn(unix_fragment, handler.get("command", ""))
                self.assertIn(windows_fragment, handler.get("commandWindows", ""))
                self.assertFalse(handler.get("async", False))
                timeout = handler.get("timeout")
                self.assertIsInstance(timeout, int)
                self.assertGreater(timeout, 0)
                self.assertLessEqual(timeout, 10)

    def test_session_end_respects_product_timeout_budget(self) -> None:
        handler = self.load_json(HOOKS_FILE)["hooks"]["SessionEnd"][0]["hooks"][0]
        self.assertLessEqual(handler["timeout"], 3)

    def test_dispatcher_exists_and_uses_only_standard_library_imports(self) -> None:
        self.assertTrue(DISPATCHER.is_file(), f"missing {DISPATCHER.relative_to(ROOT)}")
        text = DISPATCHER.read_text(encoding="utf-8")
        self.assertIn("def main", text)
        self.assertNotIn("requests", text)
        self.assertNotIn("httpx", text)

    def test_primary_plugin_manifest_still_omits_explicit_hooks_override(self) -> None:
        manifest = self.load_json(PLUGIN_MANIFEST)
        self.assertNotIn("hooks", manifest)

    def test_hook_runtime_state_is_gitignored(self) -> None:
        patterns = {
            line.strip()
            for line in GITIGNORE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        self.assertIn(".codex-kit/hooks/", patterns)

    def test_hook_packaging_has_no_machine_paths_or_placeholders(self) -> None:
        hooks_text = HOOKS_FILE.read_text(encoding="utf-8")
        dispatcher_text = DISPATCHER.read_text(encoding="utf-8")
        combined = hooks_text + dispatcher_text
        self.assertNotIn("C:\\Users\\", combined)
        self.assertNotIn("/Users/", combined)
        self.assertNotIn("/home/", combined)
        self.assertNotIn("TODO", combined)
        self.assertNotIn("TBD", combined)


if __name__ == "__main__":
    unittest.main()
