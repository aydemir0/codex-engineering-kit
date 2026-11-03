"""Exercise the real dependency checker, not a substitute AST parser."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests import test_plan_d_contract as contract


class ImportContractParserTests(unittest.TestCase):
    def check_source(self, source):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = root / "verification"
            package.mkdir()
            (package / "fixture.py").write_text(source, encoding="utf-8")
            with patch.object(contract, "REPO_ROOT", root):
                contract.PlanDContractTests().test_core_verification_and_eval_modules_use_only_stdlib_or_repo_internal_imports()

    def test_relative_project_imports_are_not_external_dependencies(self):
        for source in ("from .model import VerificationReport", "from . import model",
                       "from .nested.model import Value", "from .requests import local_helper",
                       "from typing import TYPE_CHECKING\nif TYPE_CHECKING:\n    from .model import VerificationReport"):
            with self.subTest(source=source):
                self.check_source(source)

    def test_allowed_absolute_imports_remain_allowed(self):
        self.check_source("import json\nfrom pathlib import Path\nfrom verification.model import VerificationReport")

    def test_unauthorized_absolute_imports_remain_rejected(self):
        for source in ("import requests", "from requests import get", "from model import Value",
                       "import json, prohibited_dependency", "from . import model\nimport prohibited_dependency"):
            with self.subTest(source=source), self.assertRaises(AssertionError):
                self.check_source(source)

    def test_relative_import_cannot_escape_top_level_package(self):
        for source in ("from .. import outside", "from ..requests import get", "from ...model import Value"):
            with self.subTest(source=source), self.assertRaises(AssertionError):
                self.check_source(source)


if __name__ == "__main__":
    unittest.main()
