from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.acceptance.plugin_compatibility import (
    main,
    prepare_plugin_copy,
    require_runtime_version,
    summarize_hook_events,
)

ROOT = Path(__file__).resolve().parents[1]


class PluginCompatibilityTests(unittest.TestCase):
    def test_explicit_hooks_changes_only_disposable_manifest(self) -> None:
        source_path = ROOT / ".codex-plugin" / "plugin.json"
        original = json.loads(source_path.read_text(encoding="utf-8"))
        self.assertNotIn("hooks", original)
        with tempfile.TemporaryDirectory() as temp:
            copy = prepare_plugin_copy(ROOT, Path(temp) / "plugin", "explicit-hooks")
            data = json.loads((copy / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertEqual(data["hooks"], "./hooks/hooks.json")
        self.assertEqual(json.loads(source_path.read_text(encoding="utf-8")), original)

    def test_default_variant_keeps_hooks_absent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            copy = prepare_plugin_copy(ROOT, Path(temp) / "plugin", "default")
            data = json.loads((copy / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
            self.assertNotIn("hooks", data)

    def test_runtime_version_mismatch_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            require_runtime_version("codex-cli 0.152.0", "codex-cli 0.147.0")

    def test_hook_summary_is_bounded(self) -> None:
        events = [
            {"eventName": "SessionStart", "source": "startup", "sessionId": "private-id"},
            {"eventName": "PreToolUse", "decision": "allow", "toolName": "Bash", "sessionId": "private-id"},
            {"eventName": "PostToolUse", "toolName": "Bash", "sessionId": "private-id"},
            {"eventName": "PreToolUse", "decision": "deny", "fixture": "acceptance", "toolName": "Bash", "sessionId": "private-id"},
            {"eventName": "SessionEnd", "sessionId": "private-id"},
        ]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "events.jsonl"
            path.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
            summary = summarize_hook_events(path)
        self.assertTrue(summary.session_start)
        self.assertTrue(summary.allow_seen)
        self.assertTrue(summary.post_tool_seen)
        self.assertTrue(summary.deny_fixture_seen)
        self.assertTrue(summary.session_end)
        self.assertNotIn("private-id", json.dumps(summary.to_record()))

    def test_summarize_cli_writes_only_bounded_record(self) -> None:
        events = [
            {"eventName": "SessionStart", "sessionId": "private-id"},
            {"eventName": "PreToolUse", "decision": "allow", "sessionId": "private-id"},
            {"eventName": "PostToolUse", "sessionId": "private-id"},
            {"eventName": "PreToolUse", "decision": "deny", "fixture": "acceptance", "sessionId": "private-id"},
            {"eventName": "SessionEnd", "sessionId": "private-id"},
        ]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "events.jsonl"
            output = root / "summary.json"
            source.write_text("\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8")
            code = main([
                "summarize",
                "--events", str(source),
                "--expected-runtime", "codex-cli 0.147.0",
                "--actual-runtime", "codex-cli 0.147.0",
                "--manifest-mode", "explicit-hooks",
                "--repo-sha", "0123456789abcdef0123456789abcdef01234567",
                "--output", str(output),
            ])
            record = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(code, 0)
        self.assertEqual(record["result"], "PASS")
        self.assertEqual(record["repositoryCommit"], "0123456789abcdef0123456789abcdef01234567")
        self.assertNotIn("private-id", json.dumps(record))
        self.assertNotIn("events", record)

    def test_summarize_cli_rejects_invalid_sha(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = root / "events.jsonl"
            events.write_text('{"eventName":"SessionStart","sessionId":"x"}\n', encoding="utf-8")
            code = main([
                "summarize", "--events", str(events),
                "--expected-runtime", "codex-cli 0.147.0",
                "--actual-runtime", "codex-cli 0.147.0",
                "--manifest-mode", "default",
                "--repo-sha", "bad",
                "--output", str(root / "out.json"),
            ])
        self.assertEqual(code, 1)

    def test_summarize_cli_rejects_incomplete_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            events = root / "events.jsonl"
            events.write_text('{"eventName":"SessionStart","sessionId":"one"}\n', encoding="utf-8")
            code = main([
                "summarize", "--events", str(events),
                "--expected-runtime", "codex-cli 0.147.0",
                "--actual-runtime", "codex-cli 0.147.0",
                "--manifest-mode", "default",
                "--repo-sha", "0123456789abcdef0123456789abcdef01234567",
                "--output", str(root / "out.json"),
            ])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
