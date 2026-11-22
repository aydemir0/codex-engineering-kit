"""Regression contracts for coverage-bound verification, not model benchmarks."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from verification.model import VerificationStep
from verification.package_manager import package_script_command
from verification.process import ProcessResult
from verification.python_project import discover_python_steps
from verification.runner import report_record, verify_project


ROOT = Path(__file__).resolve().parents[1]


class CoverageContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cek-verification-coverage-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def add_test_file(self, name: str, text: str) -> None:
        target = self.root / "tests"
        target.mkdir(exist_ok=True)
        (target / name).write_text(text, encoding="utf-8")

    def test_mixed_unittest_and_pytest_style_never_reports_passed(self) -> None:
        self.add_test_file(
            "test_math.py",
            "import unittest\n"
            "class Basic(unittest.TestCase):\n"
            "    def test_one(self): self.assertEqual(1, 1)\n"
            "def test_total(): assert 2 + 2 == 5\n",
        )
        report = verify_project(self.root)
        self.assertNotEqual(report.status, "passed")
        families = dict(report.test_families)
        self.assertIn("python-pytest", families)
        self.assertIn(families["python-pytest"], {"failed", "unavailable"})
        if families["python-pytest"] == "unavailable":
            self.assertEqual(families["python-unittest"], "passed")
            self.assertEqual(next(s for s in report.steps if s.name == "tests-pytest").status, "unavailable")
        self.assertIn("testFamilies", report_record(report))

    def test_pure_pytest_function_without_pytest_is_not_green(self) -> None:
        self.add_test_file("test_only.py", "def test_total(): assert 1 == 2\n")
        called: list[list[str]] = []

        def fake_runner(command, cwd):
            called.append(list(command))
            return ProcessResult(tuple(command), 0, 1, "passed", "", "")

        result = discover_python_steps(
            self.root, module_available=lambda module: False, runner=fake_runner,
        )
        self.assertEqual(dict(result.test_families), {"python-pytest": "unavailable"})
        self.assertEqual(next(s for s in result.steps if s.name == "tests").status, "unavailable")
        self.assertFalse(called, "Do not claim unittest success over a pytest-only file")

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node/npm unavailable")
    def test_mixed_node_and_failing_python_unittest_is_partial(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"name": "cek-coverage-fixture", "private": True,
                        "packageManager": "npm@10.0.0",
                        "scripts": {"test": "node -e \"process.exit(0)\""}}),
            encoding="utf-8",
        )
        self.add_test_file(
            "test_math.py",
            "import unittest\nclass Bad(unittest.TestCase):\n"
            "    def test_total(self): self.assertEqual(2 + 2, 5)\n",
        )
        report = verify_project(self.root)
        self.assertEqual(report.project_type, "node")
        self.assertEqual(report.status, "partial")
        self.assertEqual(dict(report.test_families), {"node": "passed", "python": "not-run"})
        artifact = json.loads(
            (self.root / ".codex-kit" / "verification" / "latest.json").read_text(encoding="utf-8")
        )
        self.assertEqual(
            artifact["testFamilies"],
            [
                {"family": "node", "status": "passed"},
                {"family": "python", "status": "not-run"},
            ],
        )
        self.assertEqual(
            next(s for s in report.steps if s.name == "tests-python").status,
            "unavailable",
        )
        oracle = subprocess.run(
            [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests"],
            cwd=self.root, capture_output=True, text=True, timeout=15,
        )
        self.assertNotEqual(oracle.returncode, 0)

    @unittest.skipUnless(shutil.which("pnpm") and shutil.which("node"), "pnpm/node unavailable")
    def test_pnpm_script_matches_direct_invocation(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"name": "cek-pnpm-fixture", "private": True,
                        "packageManager": "pnpm@12.21.0",
                        "scripts": {"test": 'node -e "console.log(42)"'}}),
            encoding="utf-8",
        )
        direct = subprocess.run(
            [shutil.which("pnpm"), "run", "test"],
            cwd=self.root, capture_output=True, text=True, timeout=20,
        )
        report = verify_project(self.root)
        step = next(s for s in report.steps if s.name == "tests")
        self.assertEqual(step.command, ["pnpm", "run", "test"])
        self.assertEqual(report.status, "passed")
        self.assertEqual(step.exit_code, direct.returncode)
        self.assertEqual(direct.returncode, 0)

    def test_partial_is_nonzero_only_with_require_complete(self) -> None:
        (self.root / "README.md").write_text("no configured tests\n", encoding="utf-8")
        args = [sys.executable, "-B", "-m", "verification.cli", "--project", str(self.root), "--json"]
        legacy = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True, timeout=20,
        )
        strict = subprocess.run(
            [*args, "--require-complete"], cwd=ROOT, capture_output=True,
            text=True, timeout=20,
        )
        self.assertEqual(legacy.returncode, 0)
        self.assertEqual(strict.returncode, 2)
        self.assertEqual(json.loads(strict.stdout)["status"], "partial")
        self.assertEqual(json.loads(legacy.stdout)["status"], "partial")

    def test_build_without_any_test_gate_is_partial(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps({"name": "cek-fixture", "private": True,
                        "packageManager": "npm@10.0.0",
                        "scripts": {"build": "echo ok"}}),
            encoding="utf-8",
        )
        report = verify_project(self.root)
        self.assertEqual(report.status, "partial")
        self.assertEqual(dict(report.test_families)["node"], "skipped")

    def test_unittest_zero_collected_tests_cannot_claim_green(self) -> None:
        self.add_test_file("test_empty.py", "pass\n")
        report = verify_project(self.root)
        self.assertEqual(report.status, "partial")
        self.assertEqual(dict(report.test_families), {"python-unittest": "unavailable"})
        step = next(s for s in report.steps if s.name == "tests")
        self.assertIn("zero tests", step.evidence)
        self.assertIsNone(step.exit_code)

    def test_safe_unittest_only_can_pass(self) -> None:
        self.add_test_file(
            "test_math.py",
            "import unittest\nclass Basic(unittest.TestCase):\n"
            "    def test_one(self): self.assertEqual(1, 1)\n",
        )
        report = verify_project(self.root)
        self.assertEqual(report.status, "passed")
        self.assertEqual(dict(report.test_families), {"python-unittest": "passed"})
        self.assertEqual(
            report_record(report)["testFamilies"],
            [{"family": "python-unittest", "status": "passed"}],
        )

    def test_script_arguments_are_not_augmented_for_any_package_manager(self) -> None:
        for manager in ("npm", "pnpm", "yarn", "bun"):
            with self.subTest(manager=manager):
                self.assertEqual(
                    package_script_command(manager, "test"),
                    [manager, "run", "test"],
                )


if __name__ == "__main__":
    unittest.main()
