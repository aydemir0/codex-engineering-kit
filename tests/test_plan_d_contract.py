from __future__ import annotations

import ast
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CI_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"
CASE_DIR = REPO_ROOT / "evals" / "cases"

EXPECTED_CASE_IDS = {
    "capability-verification-report",
    "regression-skipped-not-passed",
    "pressure-unsupported-performance-claim",
    "pressure-unbounded-concurrency",
    "pressure-destructive-shell-shortcut",
    "pressure-skip-tests-and-ship",
    "pressure-secret-in-repository",
}

EXECUTABLE_MODULES = {
    "verification/process.py",
    "verification/package_manager.py",
    "verification/model.py",
    "verification/node.py",
    "verification/python_project.py",
    "verification/security.py",
    "verification/git_checks.py",
    "verification/runner.py",
    "verification/cli.py",
    "evals/model.py",
    "evals/grader.py",
    "evals/runner.py",
    "evals/cli.py",
    "scripts/acceptance/codex_pressure.py",
}

INTERNAL_IMPORT_ROOTS = {"evals", "hooks", "runtime", "verification"}
PLAN_D_OS = {"ubuntu-latest", "windows-latest", "macos-latest"}
PLAN_D_COMMANDS = {
    "python -m unittest tests.test_process_runner -v",
    "python -m unittest tests.test_package_manager -v",
    "python -m unittest tests.test_verification_engine -v",
    "python -m unittest tests.test_eval_runner -v",
    "python -m unittest tests.test_codex_pressure -v",
    "python -m unittest tests.test_plan_d_contract -v",
    "python -m evals.cli offline --cases evals/cases --fixtures evals/fixtures/offline --json",
}
PINNED_ACTIONS = {
    "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
    "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
    "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
}


def _job_block(ci_text: str, job_name: str) -> str:
    match = re.search(
        rf"(?ms)^  {re.escape(job_name)}:\n(?P<body>.*?)(?=^  [A-Za-z0-9_-]+:\n|\Z)",
        ci_text,
    )
    if match is None:
        return ""
    return match.group(0)


class PlanDContractTests(unittest.TestCase):
    def test_executable_module_inventory_exists(self) -> None:
        missing = sorted(path for path in EXECUTABLE_MODULES if not (REPO_ROOT / path).is_file())
        self.assertEqual(missing, [])

    def test_eval_case_inventory_is_exact(self) -> None:
        ids = set()
        for path in CASE_DIR.glob("*.json"):
            payload = json.loads(path.read_text(encoding="utf-8"))
            ids.add(payload["id"])
        self.assertEqual(ids, EXPECTED_CASE_IDS)

    def test_verification_docs_warn_that_project_scripts_execute_with_current_permissions(self) -> None:
        path = REPO_ROOT / "docs" / "verification.md"
        self.assertTrue(path.is_file(), "docs/verification.md is required")
        text = path.read_text(encoding="utf-8").casefold()
        for gate in ("build", "test", "lint", "typecheck"):
            self.assertIn(gate, text)
        self.assertIn("repository-authored", text)
        self.assertIn("current user/codex permissions", text)

    def test_core_verification_and_eval_modules_use_only_stdlib_or_repo_internal_imports(self) -> None:
        violations: list[str] = []
        stdlib = set(sys.stdlib_module_names)
        for package in ("verification", "evals"):
            for path in sorted((REPO_ROOT / package).glob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        roots = [alias.name.split(".", 1)[0] for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.module:
                        roots = [node.module.split(".", 1)[0]]
                    else:
                        continue
                    for root in roots:
                        if root not in stdlib and root not in INTERNAL_IMPORT_ROOTS:
                            violations.append(f"{path.relative_to(REPO_ROOT)}: {root}")
        self.assertEqual(violations, [])

    def test_plan_d_ci_matrix_has_exact_three_os_and_required_deterministic_commands(self) -> None:
        ci_text = CI_PATH.read_text(encoding="utf-8")
        block = _job_block(ci_text, "plan-d-contracts")
        self.assertTrue(block, "plan-d-contracts CI job is required")

        os_match = re.search(r"os:\s*\[([^\]]+)\]", block)
        self.assertIsNotNone(os_match, "plan-d-contracts must declare an OS matrix")
        actual_os = {item.strip().strip("'\"") for item in os_match.group(1).split(",")}
        self.assertEqual(actual_os, PLAN_D_OS)
        self.assertIn("runs-on: ${{ matrix.os }}", block)
        self.assertIn("python-version: '3.11'", block)
        self.assertIn("node-version: '22'", block)

        for action in PINNED_ACTIONS:
            self.assertIn(action, block)
        for command in PLAN_D_COMMANDS:
            self.assertIn(command, block)

        self.assertNotIn("scripts/acceptance/codex_pressure.py", block)


if __name__ == "__main__":
    unittest.main()
