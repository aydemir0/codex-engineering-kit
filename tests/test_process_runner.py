from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

from verification.process import run_command


class ProcessRunnerTests(unittest.TestCase):
    def test_success_records_exit_duration_and_output(self) -> None:
        result = run_command(
            [sys.executable, "-c", "print('CEK_PROCESS_OK')"],
            Path.cwd(),
        )

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.exit_code, 0)
        self.assertGreaterEqual(result.duration_ms, 0)
        self.assertIn("CEK_PROCESS_OK", result.stdout_tail)
        self.assertEqual(result.stderr_tail, "")

    def test_nonzero_exit_is_preserved(self) -> None:
        result = run_command(
            [sys.executable, "-c", "import sys; sys.exit(7)"],
            Path.cwd(),
        )

        self.assertEqual(result.status, "failed")
        self.assertEqual(result.exit_code, 7)
        self.assertGreaterEqual(result.duration_ms, 0)

    def test_missing_executable_is_unavailable(self) -> None:
        result = run_command(
            ["cek-command-that-does-not-exist-8c0e85c7"],
            Path.cwd(),
        )

        self.assertEqual(result.status, "unavailable")
        self.assertIsNone(result.exit_code)
        self.assertIn("not found", result.reason.casefold())

    def test_timeout_is_failed_without_fabricated_exit_code(self) -> None:
        result = run_command(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            Path.cwd(),
            timeout_seconds=0.05,
        )

        self.assertEqual(result.status, "failed")
        self.assertIsNone(result.exit_code)
        self.assertIn("timeout", result.reason.casefold())

    def test_captured_streams_are_bounded_to_last_8_kib(self) -> None:
        result = run_command(
            [sys.executable, "-c", "print('A' * 12000, end='')"],
            Path.cwd(),
        )

        self.assertEqual(result.status, "passed")
        self.assertLessEqual(len(result.stdout_tail.encode("utf-8")), 8192)
        self.assertTrue(result.stdout_tail.endswith("A"))

    @unittest.skipUnless(os.name == "nt", "Windows .cmd compatibility contract")
    def test_windows_cmd_fixture_executes_through_comspec(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            script = root / "cek-fixture.cmd"
            script.write_text("@echo CEK_CMD_OK\r\n@exit /b 0\r\n", encoding="utf-8")

            result = run_command([str(script)], root)

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("CEK_CMD_OK", result.stdout_tail)


if __name__ == "__main__":
    unittest.main()
