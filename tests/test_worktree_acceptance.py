from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.acceptance.worktree_lifecycle import (
    WorktreeFixtureSafetyError,
    _remove_fixture_worktree,
    run_manual_worktree_acceptance,
)


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

    def test_dirty_source_is_not_integrated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "dirty-source.json"
            result = run_manual_worktree_acceptance(output, fixture_mode="dirty-source")

            self.assertEqual(result.status, "FAIL")
            self.assertFalse(result.clean_before_integration)
            self.assertIn("source worktree is dirty", result.blockers)
            self.assertTrue(result.cleanup_passed)
            self.assertEqual(result.remaining_fixture_worktrees, 0)

    def test_cleanup_refuses_unowned_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            repo = root / "repo"
            foreign = root / "foreign"
            repo.mkdir()
            foreign.mkdir()

            with self.assertRaises(WorktreeFixtureSafetyError):
                _remove_fixture_worktree(repo, foreign, owned=set())


if __name__ == "__main__":
    unittest.main()
