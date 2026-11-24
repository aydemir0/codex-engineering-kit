from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from verification.candidate import CandidateIntegrityError, assert_report_current
from verification.runner import VerificationScopeError, verify_project


ROOT = Path(__file__).resolve().parents[1]


class VerificationProjectRootsTests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)

    def write(self, relative: str, contents: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")
        return path

    @unittest.skipUnless(shutil.which("node") and shutil.which("npm"), "Node/npm unavailable")
    def test_separate_project_roots_share_one_candidate_report(self) -> None:
        self.write("client/package.json", json.dumps({
            "name": "verification-roots-fixture", "private": True, "packageManager": "npm",
            "scripts": {"test": "node check.cjs"},
        }))
        self.write("client/check.cjs", "require('node:assert/strict').equal(3 + 4, 7);\n")
        sentinel = self.write("unrelated.txt", "preserve this evidence\n")
        test = "import unittest\nclass Core(unittest.TestCase):\n"
        service = self.write("services/api/tests/test_core.py", test +
                             "    def test_total(self): self.assertEqual(3 + 4, 6)\n")
        result = subprocess.run(
            [sys.executable, "-B", "-m", "verification.cli", "--project", str(self.root),
             "--include-project", "client", "--include-project", "services/api",
             "--json", "--require-complete"],
            cwd=ROOT, capture_output=True, text=True, timeout=35,
        )
        artifact = json.loads(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(artifact["projectType"], "multi-root")
        self.assertEqual(artifact["projectRoots"], ["client", "services/api"])
        self.assertEqual(artifact["testFamilies"], [
            {"family": "client:node", "status": "passed"},
            {"family": "services/api:python-unittest", "status": "failed"},
        ])
        self.assertFalse((service.parents[1] / ".codex-kit").exists())
        self.write("services/api/tests/test_core.py", test +
                   "    def test_total(self): self.assertEqual(3 + 4, 7)\n")
        report = verify_project(self.root, project_roots=("client", "services/api"))
        self.assertEqual(report.status, "passed")
        self.assertIn("services/api/tests/test_core.py", {row[0] for row in report.candidate_manifest})
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve this evidence\n")
        self.write("services/api/tests/test_core.py", test +
                   "    def test_total(self): self.assertEqual(3 + 4, 6)\n")
        with self.assertRaisesRegex(CandidateIntegrityError, "VERIFICATION_STALE"):
            assert_report_current(self.root, report)

    def test_invalid_project_roots_fail_before_any_report_write(self) -> None:
        self.write("client/subdir/readme.txt", "existing child")
        for roots in (
            (".",),
            ("../client",),
            (str(self.root / "client"),),
            ("missing",),
            ("client", "client"),
            ("client/subdir", "client"),
            ("client", "client/subdir"),
        ):
            with self.subTest(roots=roots), self.assertRaises(VerificationScopeError):
                verify_project(self.root, project_roots=roots)
        self.assertFalse((self.root / ".codex-kit").exists())

    def test_root_manifest_must_cover_selected_files(self) -> None:
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".gitignore", "local/\n")
        self.write("local/pyproject.toml", "[project]\nname='fixture'\nversion='0'\n")
        with self.assertRaisesRegex(VerificationScopeError, "outside the root candidate"):
            verify_project(self.root, project_roots=("local",))

    def test_unrecognized_project_root_prevents_a_pass(self) -> None:
        self.write("service/tests/test_core.py",
                   "import unittest\nclass Core(unittest.TestCase):\n"
                   "    def test_total(self): self.assertEqual(3 + 4, 7)\n")
        self.write("unknown/README.md", "no recognized tests")
        report = verify_project(self.root, project_roots=("service", "unknown"))
        self.assertEqual(report.status, "partial")
        self.assertEqual(dict(report.test_families), {
            "service:python-unittest": "passed",
            "unknown:tests": "unavailable",
        })
