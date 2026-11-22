"""End-to-end hook stdin trust-boundary checks, independent of dispatch unit tests."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from hooks.scripts.hook_dispatch import main


def invoke_hook(host: Path, supplied_cwd: str) -> tuple[int, str, str]:
    payload = {
        "hook_event_name": "PostToolUse",
        "session_id": "fixture-session",
        "cwd": supplied_cwd,
        "tool_input": {"command": "echo should-not-be-copied"},
    }
    out, err = io.StringIO(), io.StringIO()
    with (
        patch("hooks.scripts.hook_dispatch.Path.cwd", return_value=host),
        patch.object(sys, "stdin", io.StringIO(json.dumps(payload))),
        contextlib.redirect_stdout(out),
        contextlib.redirect_stderr(err),
    ):
        code = main()
    return code, out.getvalue(), err.getvalue()


class HookEntrypointBoundaryTests(unittest.TestCase):
    def test_matching_host_cwd_writes_only_bounded_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            host = Path(tmp)
            code, stdout, stderr = invoke_hook(host, str(host))
            self.assertEqual(code, 0, stderr)
            self.assertEqual(json.loads(stdout), {})
            state = host / ".codex-kit" / "hooks" / "events.jsonl"
            self.assertTrue(state.is_file())
            self.assertNotIn("should-not-be-copied", state.read_text(encoding="utf-8"))

    def test_forged_cwd_cannot_redirect_state_to_sibling(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, outside = root / "host", root / "outside"
            host.mkdir()
            outside.mkdir()
            code, stdout, stderr = invoke_hook(host, str(outside))
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertIn("does not match", stderr)
            self.assertFalse((outside / ".codex-kit").exists())
            self.assertFalse((host / ".codex-kit").exists())

    def test_relative_and_parent_traversal_paths_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, sibling = root / "host", root / "sibling"
            host.mkdir()
            sibling.mkdir()
            for path in ("../sibling", str(host / ".." / "sibling")):
                with self.subTest(path=path):
                    code, stdout, stderr = invoke_hook(host, path)
                    self.assertEqual(code, 1)
                    self.assertEqual(stdout, "")
                    self.assertIn("absolute, normalized", stderr)
            self.assertFalse((sibling / ".codex-kit").exists())

    def test_nonexistent_workspace_is_rejected_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host = root / "host"
            host.mkdir()
            absent = root / "absent"
            code, stdout, _ = invoke_hook(host, str(absent))
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertFalse(absent.exists())

    def test_real_hook_subprocess_binds_workspace_and_rejects_forgery(self) -> None:
        plugin_root = Path(__file__).resolve().parents[1]
        executable = plugin_root / "hooks" / "scripts" / "hook_dispatch.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, outside = root / "host", root / "outside"
            host.mkdir()
            outside.mkdir()
            for cwd, expected_exit in ((str(host), 0), (str(outside), 1)):
                with self.subTest(expected_exit=expected_exit):
                    payload = json.dumps({
                        "hook_event_name": "PostToolUse",
                        "session_id": "fixture-session",
                        "cwd": cwd,
                    })
                    result = subprocess.run(
                        [sys.executable, "-B", str(executable)],
                        input=payload,
                        cwd=host,
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    self.assertEqual(result.returncode, expected_exit, result.stderr)
            self.assertTrue((host / ".codex-kit" / "hooks" / "events.jsonl").is_file())
            self.assertFalse((outside / ".codex-kit").exists())

    def test_reparse_workspace_alias_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            host, alias = root / "host", root / "alias"
            host.mkdir()
            if os.name == "nt":
                result = subprocess.run(
                    ["cmd.exe", "/d", "/c", "mklink", "/J", str(alias), str(host)],
                    capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            else:
                alias.symlink_to(host, target_is_directory=True)
            code, stdout, stderr = invoke_hook(alias, str(alias))
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertIn("unsafe state path", stderr)
            self.assertFalse((host / ".codex-kit").exists())

            code, stdout, stderr = invoke_hook(host, str(alias))
            self.assertEqual(code, 1)
            self.assertEqual(stdout, "")
            self.assertIn("does not match", stderr)
            self.assertFalse((host / ".codex-kit").exists())


if __name__ == "__main__":
    unittest.main()
