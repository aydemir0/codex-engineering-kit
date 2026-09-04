from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.acceptance.worktree_lifecycle import run_manual_worktree_acceptance


class ManualWorktreeAcceptanceTests(unittest.TestCase):
    def test_disposable_manual_git_lifecycle_isolated_conflict_stopped_and_cleaned(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "worktree-acceptance.json"
            result = run_manual_worktree_acceptance(output)

            self.assertEqual(result.status, "PASS")
            self.assertTrue(result.detached_creation)
            self.assertTrue(result.unique_branches)
            self.assertTrue(result.isolated_writes)
            self.assertTrue(result.clean_before_integration)
            self.assertTrue(result.conflict_stopped)
            self.assertTrue(result.cleanup_passed)
            self.assertEqual(result.remaining_fixture_worktrees, 0)
            self.assertEqual(result.blockers, ())

            artifact = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(artifact["schemaVersion"], 1)
            self.assertEqual(artifact["kind"], "worktree-acceptance")
            self.assertEqual(artifact["mode"], "manual-git")
            self.assertEqual(artifact["status"], "PASS")

            raw = output.read_text(encoding="utf-8").casefold()
            self.assertNotIn("\\users\\", raw)
            self.assertNotIn("/home/", raw)
            self.assertNotIn("/tmp/", raw)
            self.assertNotIn("appdata", raw)


if __name__ == "__main__":
    unittest.main()
