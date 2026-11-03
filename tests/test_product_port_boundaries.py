"""Mainline-only port boundaries: no implicit authority or experimental imports."""
import ast
import os
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from runtime.assurance.model import Permission
from runtime.workflow.coordinator import TransitionError, require_m2a_authority
from runtime.workflow.command import run_workflow
from runtime.workflow.command import workflow_ledger_path
from runtime.workflow.profile import create_profile, WorkflowProfileError
from scripts.cek_workflow import _parser

class ProductPortBoundaryTests(unittest.TestCase):
    def test_workflow_identity_cannot_select_parent_directory(self):
        for identity in (".", ".."):
            with self.subTest(identity=identity), self.assertRaises(ValueError):
                workflow_ledger_path(Path("owned-root"), identity)

    def test_owned_profile_cannot_be_reopened_through_indirection(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            profile = root / "owned-profile"
            normal, project = root / "normal", root / "project"
            create_profile(profile, normal, project, "test", "a" * 40)
            sentinel = profile / "sentinel.txt"
            sentinel.write_bytes(b"foreign-owner")
            link = root / "redirected-profile"
            if os.name == "nt":
                subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(profile)],
                               check=True, capture_output=True)
            else:
                link.symlink_to(profile, target_is_directory=True)
            try:
                with self.assertRaises(WorkflowProfileError):
                    create_profile(link, normal, project, "test", "a" * 40)
                self.assertEqual(sentinel.read_bytes(), b"foreign-owner")
            finally:
                if os.name == "nt":
                    link.rmdir()
                else:
                    link.unlink()

    def test_missing_or_non_boolean_authorization_fails_closed(self):
        for authority in [None, object(), SimpleNamespace(authorize=lambda _: None),
                          SimpleNamespace(authorize=lambda p: SimpleNamespace(permissions={p: "yes"})),
                          SimpleNamespace(authorize=lambda p: SimpleNamespace(permissions={p: False}))]:
            with self.subTest(authority=type(authority).__name__):
                with self.assertRaises(TransitionError):
                    require_m2a_authority(authority)

    def test_both_permissions_remain_required(self):
        calls = []
        def authorize(permission):
            calls.append(permission)
            return SimpleNamespace(permissions={permission: True})
        require_m2a_authority(SimpleNamespace(authorize=authorize))
        self.assertEqual(calls, [Permission.ORCHESTRATION, Permission.MANAGED_WORKTREE])

    def test_native_execution_cannot_start_without_authority(self):
        runner = Mock()
        with self.assertRaises(TransitionError):
            run_workflow(profile_root=Path("unused-profile"), normal_codex_home=Path("unused-home"),
                         project=Path("unused-project"), workflow_id="local-test", task="local test",
                         cek_sha="a"*40, base_commit_sha="b"*40, runtime_identity={},
                         commands=("local",), scope=("local",), executable=Path("unused-runtime"),
                         authority=None, runner=runner)
        runner.assert_not_called()

    def test_cli_cannot_implicitly_authorize_execution(self):
        with self.assertRaises(SystemExit):
            _parser().parse_args(["workflow", "run", "--workflow-root", "unused", "--workflow-id", "unused"])

    def test_production_foundation_has_no_experimental_imports(self):
        root = Path(__file__).resolve().parents[1]
        files = list((root/"runtime/workflow").glob("*.py"))
        files += list((root/"runtime/assurance").glob("*.py"))
        files += [root/"runtime/diagnostics/native_failure.py", root/"scripts/cek_workflow.py"]
        for path in files:
            for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                names = [node.module or ""] if isinstance(node, ast.ImportFrom) else [a.name for a in node.names] if isinstance(node, ast.Import) else []
                self.assertFalse(any(n.startswith(("benchmarks", "release_contracts")) for n in names), str(path))
