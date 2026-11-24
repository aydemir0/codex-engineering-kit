"""Regression contracts for coverage-bound verification, not model benchmarks."""
from __future__ import annotations

import json
import os
import py_compile
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

    def add_mixed_contract_fixture(self, node_expected: int, python_expected: int) -> Path:
        (self.root / "package.json").write_text(
            json.dumps({"name": "cek-coverage-fixture", "private": True,
                        "packageManager": "npm@10.0.0",
                        "scripts": {"test": "node check-contract.js"}}),
            encoding="utf-8",
        )
        (self.root / "check-contract.js").write_text(
            "const assert = require('node:assert/strict');\n"
            f"assert.equal(require('./contract.json').version, {node_expected});\n",
            encoding="utf-8",
        )
        (self.root / "contract.json").write_text('{"version": 2}\n', encoding="utf-8")
        self.add_test_file(
            "test_contract.py",
            "import json\nimport unittest\nfrom pathlib import Path\n"
            "class ContractTests(unittest.TestCase):\n"
            "    def test_version(self):\n"
            "        contract = Path(__file__).resolve().parents[1] / 'contract.json'\n"
            f"        self.assertEqual(json.loads(contract.read_text())['version'], {python_expected})\n",
        )
        sentinel = self.root / "foreign.txt"
        sentinel.write_bytes(b"preserve this file\n")
        return sentinel

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node/npm unavailable")
    def test_mixed_contract_requires_both_real_suites(self) -> None:
        for node_expected, python_expected, expected_status in (
            (2, 2, "passed"),
            (2, 1, "failed"),
            (1, 2, "failed"),
        ):
            with self.subTest(node_expected=node_expected, python_expected=python_expected):
                sentinel = self.add_mixed_contract_fixture(node_expected, python_expected)
                report = verify_project(self.root)
                self.assertEqual(report.project_type, "node")
                self.assertEqual(report.status, expected_status)
                families = {
                    "node": "passed" if node_expected == 2 else "failed",
                    "python-unittest": "passed" if python_expected == 2 else "failed",
                }
                self.assertEqual(dict(report.test_families), families)
                artifact = json.loads(
                    (self.root / ".codex-kit" / "verification" / "latest.json").read_text(encoding="utf-8")
                )
                self.assertEqual({row["family"]: row["status"] for row in artifact["testFamilies"]}, families)
                steps = {step.name: step for step in report.steps}
                self.assertEqual(len(steps), len(report.steps))
                self.assertEqual(steps["tests"].status, families["node"])
                self.assertEqual(steps["tests-python"].status, families["python-unittest"])
                self.assertIn("Ran 1 test", steps["tests-python"].evidence)
                self.assertEqual(sentinel.read_bytes(), b"preserve this file\n")

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node/npm unavailable")
    def test_mixed_contract_without_python_tests_stays_partial(self) -> None:
        self.add_mixed_contract_fixture(2, 2)
        (self.root / "tests" / "test_contract.py").unlink()
        (self.root / "pyproject.toml").write_text(
            "[build-system]\nrequires = []\nbuild-backend = 'example'\n", encoding="utf-8"
        )
        report = verify_project(self.root)
        self.assertEqual(report.status, "partial")
        self.assertEqual(dict(report.test_families), {"node": "passed", "python": "skipped"})
        self.assertFalse(any(step.name == "build-python" for step in report.steps))

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node/npm unavailable")
    def test_mixed_contract_runs_source_when_timestamp_bytecode_is_stale(self) -> None:
        self.add_mixed_contract_fixture(2, 2)
        source = self.root / "tests" / "test_contract.py"
        original = source.stat()
        cached = Path(py_compile.compile(
            str(source), doraise=True,
            invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP,
        ))
        cache_bytes = cached.read_bytes()
        self.add_mixed_contract_fixture(2, 1)
        os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns))
        self.assertEqual(source.stat().st_size, original.st_size)

        report = verify_project(self.root)

        self.assertEqual(report.status, "failed")
        self.assertEqual(dict(report.test_families), {"node": "passed", "python-unittest": "failed"})
        self.assertEqual(cached.read_bytes(), cache_bytes)

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node/npm unavailable")
    def test_mixed_contract_includes_root_unittest_alongside_tests_directory(self) -> None:
        self.add_mixed_contract_fixture(2, 2)
        (self.root / "test_root_contract.py").write_text(
            "import unittest\nclass RootContract(unittest.TestCase):\n"
            "    def test_version(self): self.assertEqual(2, 1)\n",
            encoding="utf-8",
        )
        result = subprocess.run(
            [sys.executable, "-B", "-m", "verification.cli", "--project", str(self.root),
             "--json", "--require-complete"],
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1, data)
        self.assertEqual(data["status"], "failed")
        self.assertIn({"family": "python-unittest-root", "status": "failed"}, data["testFamilies"])

    def test_unittest_candidate_outside_discovery_layout_is_partial(self) -> None:
        tests = self.root / "tests"
        tests.mkdir()
        self.add_test_file(
            "test_math.py",
            "import unittest\nclass Math(unittest.TestCase):\n"
            "    def test_total(self): self.assertEqual(2 + 2, 4)\n",
        )
        nested = tests / "nested"
        nested.mkdir()
        (nested / "test_missing.py").write_text(
            "import unittest\nclass Missing(unittest.TestCase):\n"
            "    def test_failure(self): self.assertEqual(2 + 2, 5)\n",
            encoding="utf-8",
        )
        report = verify_project(self.root)
        self.assertEqual(report.status, "partial")
        self.assertEqual(
            dict(report.test_families),
            {"python-unittest": "passed", "python-unittest-layout": "unavailable"},
        )

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

    def test_unittest_with_only_skips_is_partial_for_tree_and_root(self) -> None:
        source = (
            "import unittest\nclass Skipped(unittest.TestCase):\n"
            "    @unittest.skip('fixture is unavailable')\n"
            "    def test_calculation(self): self.fail()\n"
        )
        for layout, family in (("tests/test_only.py", "python-unittest"),
                               ("test_only.py", "python-unittest-root")):
            with self.subTest(layout=layout), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                path = root / layout
                path.parent.mkdir(exist_ok=True)
                path.write_text(source, encoding="utf-8")
                report = verify_project(root)
                self.assertEqual(report.status, "partial")
                self.assertEqual(dict(report.test_families), {family: "unavailable"})

    def test_unittest_with_some_skips_and_a_pass_stays_passed(self) -> None:
        self.add_test_file(
            "test_math.py",
            "import unittest\nclass Math(unittest.TestCase):\n"
            "    @unittest.skip('fixture is unavailable')\n"
            "    def test_skipped(self): self.fail()\n"
            "    def test_calculation(self): self.assertEqual(2 + 2, 4)\n",
        )
        self.assertEqual(verify_project(self.root).status, "passed")

    def test_pytest_needs_a_summary_with_a_passing_test(self) -> None:
        self.add_test_file("test_math.py", "def test_calculation(): pass\n")
        cases = [("s [100%]", "unavailable"), (". [100%]", "unavailable")]
        for count in (1, 2, 100):
            for suffix, expected in (
                ("", "unavailable"),
                (", 2 warnings", "unavailable"),
                (", 1 passed", "passed"),
            ):
                summary = f"\x1b[33m=== {count} skipped{suffix} in 0.15s ===\x1b[0m"
                cases.append((summary, expected))

        for summary, expected in cases:
            def runner(command, cwd):
                return ProcessResult(tuple(command), 0, 1, "passed", summary, "")

            with self.subTest(summary=summary):
                result = discover_python_steps(
                    self.root, module_available=lambda package: package == "pytest", runner=runner,
                )
                self.assertEqual(dict(result.test_families), {"python-pytest": expected})

    def test_script_arguments_are_not_augmented_for_any_package_manager(self) -> None:
        for manager in ("npm", "pnpm", "yarn", "bun"):
            with self.subTest(manager=manager):
                self.assertEqual(
                    package_script_command(manager, "test"),
                    [manager, "run", "test"],
                )


if __name__ == "__main__":
    unittest.main()
