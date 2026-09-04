from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from verification.git_checks import run_git_diff_check
from verification.node import discover_node_steps
from verification.process import ProcessResult
from verification.python_project import discover_python_steps
from verification.runner import verify_project
from verification.security import scan_secret_patterns


class VerificationNodeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_package(self, scripts: dict[str, str], package_manager: str = "npm@10.0.0") -> None:
        (self.root / "package.json").write_text(
            json.dumps(
                {
                    "name": "cek-node-fixture",
                    "private": True,
                    "packageManager": package_manager,
                    "scripts": scripts,
                }
            ),
            encoding="utf-8",
        )

    @staticmethod
    def which_with(*available: str):
        available_set = set(available)

        def resolve(name: str) -> str | None:
            return f"/fake/bin/{name}" if name in available_set else None

        return resolve

    def test_discovers_aliases_executes_selected_scripts_and_skips_missing_gate(self) -> None:
        self.write_package(
            {
                "build": "node -e \"process.exit(0)\"",
                "type-check": "node -e \"process.exit(0)\"",
                "test": "node -e \"process.exit(0)\"",
            }
        )
        seen: list[list[str]] = []

        def runner(command, cwd, timeout_seconds=120):
            seen.append(list(command))
            return ProcessResult(
                command=tuple(command),
                exit_code=0,
                duration_ms=4,
                status="passed",
                stdout_tail="",
                stderr_tail="",
            )

        result = discover_node_steps(
            self.root,
            which=self.which_with("npm"),
            runner=runner,
        )
        by_name = {step.name: step for step in result.steps}

        self.assertEqual(result.package_manager, "npm")
        self.assertEqual(result.manager_source, "packageManager")
        self.assertEqual(by_name["build"].status, "passed")
        self.assertEqual(by_name["typecheck"].status, "passed")
        self.assertEqual(by_name["tests"].status, "passed")
        self.assertEqual(by_name["lint"].status, "skipped")
        self.assertIsNone(by_name["lint"].command)
        self.assertEqual(
            seen,
            [
                ["npm", "run", "build", "--silent"],
                ["npm", "run", "type-check", "--silent"],
                ["npm", "run", "test", "--silent"],
            ],
        )
        self.assertTrue(all(step.duration_ms >= 0 for step in result.steps))

    def test_alias_priority_prefers_primary_typecheck_and_test_names(self) -> None:
        self.write_package(
            {
                "typecheck": "node -e \"process.exit(0)\"",
                "type-check": "node -e \"process.exit(0)\"",
                "check-types": "node -e \"process.exit(0)\"",
                "test": "node -e \"process.exit(0)\"",
                "tests": "node -e \"process.exit(0)\"",
            }
        )
        seen: list[list[str]] = []

        def runner(command, cwd, timeout_seconds=120):
            seen.append(list(command))
            return ProcessResult(tuple(command), 0, 1, "passed", "", "")

        discover_node_steps(
            self.root,
            which=self.which_with("npm"),
            runner=runner,
        )

        self.assertIn(["npm", "run", "typecheck", "--silent"], seen)
        self.assertNotIn(["npm", "run", "type-check", "--silent"], seen)
        self.assertNotIn(["npm", "run", "check-types", "--silent"], seen)
        self.assertIn(["npm", "run", "test", "--silent"], seen)
        self.assertNotIn(["npm", "run", "tests", "--silent"], seen)

    def test_authoritative_missing_manager_marks_discovered_gate_unavailable(self) -> None:
        self.write_package(
            {"test": "node -e \"process.exit(0)\""},
            package_manager="yarn@4.6.0",
        )
        called = False

        def runner(command, cwd, timeout_seconds=120):
            nonlocal called
            called = True
            raise AssertionError("unavailable manager must not execute")

        result = discover_node_steps(
            self.root,
            which=self.which_with("npm"),
            runner=runner,
        )
        by_name = {step.name: step for step in result.steps}

        self.assertFalse(called)
        self.assertEqual(result.package_manager, "yarn")
        self.assertEqual(result.manager_detail, "unavailable")
        self.assertEqual(by_name["tests"].status, "unavailable")
        self.assertEqual(by_name["tests"].command, ["yarn", "run", "test", "--silent"])
        self.assertIsNone(by_name["tests"].exit_code)
        self.assertEqual(by_name["build"].status, "skipped")

    def test_ambiguous_lockfiles_do_not_guess_a_manager(self) -> None:
        self.write_package({"test": "node -e \"process.exit(0)\""}, package_manager="")
        data = json.loads((self.root / "package.json").read_text(encoding="utf-8"))
        data.pop("packageManager")
        (self.root / "package.json").write_text(json.dumps(data), encoding="utf-8")
        (self.root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        (self.root / "yarn.lock").write_text("", encoding="utf-8")

        result = discover_node_steps(
            self.root,
            which=self.which_with("pnpm", "yarn", "npm"),
            runner=lambda *args, **kwargs: self.fail("ambiguous manager must not execute"),
        )
        by_name = {step.name: step for step in result.steps}

        self.assertIsNone(result.package_manager)
        self.assertEqual(result.manager_detail, "ambiguous-lockfiles")
        self.assertEqual(by_name["tests"].status, "unavailable")
        self.assertIsNone(by_name["tests"].command)

    def test_failed_process_result_preserves_exit_duration_and_bounded_evidence(self) -> None:
        self.write_package({"test": "node -e \"process.exit(7)\""})

        def runner(command, cwd, timeout_seconds=120):
            return ProcessResult(
                command=tuple(command),
                exit_code=7,
                duration_ms=13,
                status="failed",
                stdout_tail="",
                stderr_tail="fixture failed",
            )

        result = discover_node_steps(
            self.root,
            which=self.which_with("npm"),
            runner=runner,
        )
        tests_step = next(step for step in result.steps if step.name == "tests")

        self.assertEqual(tests_step.status, "failed")
        self.assertEqual(tests_step.exit_code, 7)
        self.assertEqual(tests_step.duration_ms, 13)
        self.assertEqual(tests_step.evidence, "fixture failed")


class VerificationPythonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def passed_runner(seen: list[list[str]]):
        def runner(command, cwd, timeout_seconds=120):
            seen.append(list(command))
            return ProcessResult(tuple(command), 0, 2, "passed", "", "")

        return runner

    def test_build_system_without_build_module_is_unavailable(self) -> None:
        (self.root / "pyproject.toml").write_text(
            "[build-system]\nrequires = []\nbuild-backend = 'cek.backend'\n",
            encoding="utf-8",
        )

        result = discover_python_steps(
            self.root,
            module_available=lambda name: False,
            runner=lambda *args, **kwargs: self.fail("missing build module must not execute"),
        )
        by_name = {step.name: step for step in result.steps}

        self.assertEqual(by_name["build"].status, "unavailable")
        self.assertEqual(by_name["build"].command, [sys.executable, "-m", "build"])
        self.assertIn("build", by_name["build"].evidence)

    def test_pytest_marker_without_pytest_module_is_unavailable(self) -> None:
        (self.root / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")

        result = discover_python_steps(
            self.root,
            module_available=lambda name: False,
            runner=lambda *args, **kwargs: self.fail("missing pytest module must not execute"),
        )
        by_name = {step.name: step for step in result.steps}

        self.assertEqual(by_name["tests"].status, "unavailable")
        self.assertEqual(by_name["tests"].command, [sys.executable, "-m", "pytest"])

    def test_unittest_fallback_discovers_test_tree_without_pytest_marker(self) -> None:
        tests_dir = self.root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_example.py").write_text("pass\n", encoding="utf-8")
        seen: list[list[str]] = []

        result = discover_python_steps(
            self.root,
            module_available=lambda name: False,
            runner=self.passed_runner(seen),
        )
        by_name = {step.name: step for step in result.steps}

        self.assertEqual(by_name["tests"].status, "passed")
        self.assertIn(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            seen,
        )

    def test_ruff_and_mypy_require_both_configuration_and_available_module(self) -> None:
        (self.root / "pyproject.toml").write_text(
            "[tool.ruff]\nline-length = 100\n\n[tool.mypy]\nstrict = true\n",
            encoding="utf-8",
        )
        seen: list[list[str]] = []

        result = discover_python_steps(
            self.root,
            module_available=lambda name: name in {"ruff", "mypy"},
            runner=self.passed_runner(seen),
        )
        by_name = {step.name: step for step in result.steps}

        self.assertEqual(by_name["lint"].status, "passed")
        self.assertEqual(by_name["typecheck"].status, "passed")
        self.assertIn([sys.executable, "-m", "ruff", "check", "."], seen)
        self.assertIn([sys.executable, "-m", "mypy", "."], seen)
        self.assertEqual(by_name["build"].status, "skipped")
        self.assertEqual(by_name["tests"].status, "skipped")

    def test_configured_ruff_and_mypy_are_skipped_when_modules_are_unavailable(self) -> None:
        (self.root / "pyproject.toml").write_text(
            "[tool.ruff]\nline-length = 100\n\n[tool.mypy]\nstrict = true\n",
            encoding="utf-8",
        )

        result = discover_python_steps(
            self.root,
            module_available=lambda name: False,
            runner=lambda *args, **kwargs: self.fail("optional unavailable tools must not execute"),
        )
        by_name = {step.name: step for step in result.steps}

        self.assertEqual(by_name["lint"].status, "skipped")
        self.assertEqual(by_name["typecheck"].status, "skipped")


class VerificationGenericChecksTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_secret_scan_fails_on_synthetic_token_and_excludes_runtime_state(self) -> None:
        fake_secret = "ghp_" + ("A" * 24)
        (self.root / "app.py").write_text(f"TOKEN = '{fake_secret}'\n", encoding="utf-8")
        runtime_dir = self.root / ".codex-kit"
        runtime_dir.mkdir()
        (runtime_dir / "ignored.txt").write_text(fake_secret, encoding="utf-8")

        result = scan_secret_patterns(self.root)

        self.assertEqual(result.name, "security")
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.exit_code, 1)
        self.assertIn("app.py", result.evidence)
        self.assertNotIn(".codex-kit", result.evidence)

    def test_secret_scan_passes_when_only_excluded_tree_contains_fixture(self) -> None:
        fake_secret = "ghp_" + ("B" * 24)
        runtime_dir = self.root / ".codex-kit"
        runtime_dir.mkdir()
        (runtime_dir / "ignored.txt").write_text(fake_secret, encoding="utf-8")

        result = scan_secret_patterns(self.root)

        self.assertEqual(result.status, "passed")
        self.assertEqual(result.exit_code, 0)

    def test_git_diff_check_preserves_real_failure_exit_code(self) -> None:
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "cek@example.invalid"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "CEK Fixture"],
            cwd=self.root,
            check=True,
        )
        tracked = self.root / "tracked.txt"
        tracked.write_text("clean\n", encoding="utf-8")
        subprocess.run(["git", "add", "tracked.txt"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-m", "fixture"],
            cwd=self.root,
            check=True,
            capture_output=True,
        )
        tracked.write_text("bad trailing whitespace   \n", encoding="utf-8")

        result = run_git_diff_check(self.root)

        self.assertEqual(result.name, "diff")
        self.assertEqual(result.status, "failed")
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("whitespace", result.evidence.casefold())

    def test_git_diff_check_is_skipped_outside_worktree(self) -> None:
        result = run_git_diff_check(self.root)

        self.assertEqual(result.status, "skipped")
        self.assertIsNone(result.exit_code)


class VerificationOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_node_classification_beats_python_markers_and_writes_versioned_artifact(self) -> None:
        (self.root / "package.json").write_text(
            json.dumps(
                {
                    "name": "cek-orchestrator",
                    "private": True,
                    "packageManager": "npm@10.0.0",
                    "scripts": {},
                }
            ),
            encoding="utf-8",
        )
        (self.root / "pyproject.toml").write_text("[project]\nname = 'also-python'\n", encoding="utf-8")

        report = verify_project(self.root)

        self.assertEqual(report.schema_version, 1)
        self.assertEqual(report.project_type, "node")
        artifact_path = self.root / ".codex-kit" / "verification" / "latest.json"
        self.assertTrue(artifact_path.is_file())
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["schemaVersion"], 1)
        self.assertEqual(artifact["kind"], "verification-report")
        self.assertEqual(artifact["projectType"], "node")
        self.assertEqual(artifact["status"], report.status)
        self.assertEqual(len(artifact["steps"]), len(report.steps))
        for step in artifact["steps"]:
            self.assertEqual(
                set(step),
                {"name", "command", "status", "exitCode", "durationMs", "evidence"},
            )
            self.assertIn(step["status"], {"passed", "failed", "skipped", "unavailable"})
            self.assertGreaterEqual(step["durationMs"], 0)
            self.assertLessEqual(len(step["evidence"].encode("utf-8")), 8192)

    def test_python_markers_classify_python_when_package_json_is_absent(self) -> None:
        (self.root / "pyproject.toml").write_text("[project]\nname = 'cek-python'\n", encoding="utf-8")

        report = verify_project(self.root)

        self.assertEqual(report.project_type, "python")

    def test_repository_without_language_markers_is_generic(self) -> None:
        (self.root / "README.md").write_text("generic\n", encoding="utf-8")

        report = verify_project(self.root)

        self.assertEqual(report.project_type, "generic")

    def test_failed_security_step_fails_report(self) -> None:
        fake_secret = "ghp_" + ("C" * 24)
        (self.root / "app.py").write_text(f"TOKEN = '{fake_secret}'\n", encoding="utf-8")

        report = verify_project(self.root)

        by_name = {step.name: step for step in report.steps}
        self.assertEqual(by_name["security"].status, "failed")
        self.assertEqual(report.status, "failed")

    def test_cli_json_is_sorted_writes_requested_output_and_failed_report_exits_one(self) -> None:
        fake_secret = "ghp_" + ("D" * 24)
        (self.root / "app.py").write_text(f"TOKEN = '{fake_secret}'\n", encoding="utf-8")
        output_path = self.root / "custom-report.json"

        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "verification.cli",
                "--project",
                str(self.root),
                "--json",
                "--output",
                str(output_path),
            ],
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(completed.returncode, 1)
        stdout = completed.stdout.strip()
        self.assertEqual(stdout, json.dumps(json.loads(stdout), sort_keys=True, separators=(",", ":")))
        self.assertTrue(output_path.is_file())
        payload = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual(payload["schemaVersion"], 1)
        self.assertEqual(payload["kind"], "verification-report")
        self.assertEqual(payload["status"], "failed")


if __name__ == "__main__":
    unittest.main()
