from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from verification.node import discover_node_steps
from verification.process import ProcessResult


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


if __name__ == "__main__":
    unittest.main()
