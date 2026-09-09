from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from runtime.state import read_state, write_state


class StateContractTests(unittest.TestCase):
    def link_directory(self, link: Path, target: Path) -> None:
        if os.name == "nt":
            subprocess.run(
                ["cmd.exe", "/d", "/c", "mklink", "/J", str(link), str(target)],
                check=True,
                capture_output=True,
                text=True,
            )
        else:
            link.symlink_to(target, target_is_directory=True)

    def test_round_trip_preserves_current_schema_and_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            write_state(path, "fixture", {"value": "ok"})

            record, reason = read_state(path, "fixture")

        self.assertIsNone(reason)
        self.assertEqual(record, {"schemaVersion": 1, "kind": "fixture", "value": "ok"})

    def test_payload_cannot_override_reserved_state_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            write_state(
                path,
                "trusted-kind",
                {"schemaVersion": 999, "kind": "attacker-kind", "value": "ok"},
            )
            record = json.loads(path.read_text(encoding="utf-8"))

        self.assertEqual(record["schemaVersion"], 1)
        self.assertEqual(record["kind"], "trusted-kind")

    def test_unknown_schema_fails_closed_with_bounded_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(
                json.dumps(
                    {
                        "schemaVersion": 999,
                        "kind": "fixture",
                        "private": "DO_NOT_ECHO_THIS_VALUE",
                    }
                ),
                encoding="utf-8",
            )

            record, reason = read_state(path, "fixture")

        self.assertIsNone(record)
        self.assertEqual(reason, "unsupported-schema")
        self.assertNotIn("DO_NOT_ECHO_THIS_VALUE", reason)

    def test_write_rejects_linked_ancestor_before_creating_descendants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            outside = root / "outside"
            workspace.mkdir()
            outside.mkdir()
            self.link_directory(workspace / ".codex-kit", outside)
            path = workspace / ".codex-kit" / "evals" / "offline" / "latest.json"

            with self.assertRaisesRegex(ValueError, "unsafe state path"):
                write_state(path, "fixture", {"value": "ok"})

            self.assertFalse((outside / "evals").exists())


if __name__ == "__main__":
    unittest.main()
