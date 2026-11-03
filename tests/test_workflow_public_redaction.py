"""Cross-platform public evidence redaction; no real credentials or private paths."""
import json
from pathlib import Path, PurePosixPath
import tempfile
import unittest

from runtime.workflow.ledger import WorkflowLedger, _sanitize_text
from tests import test_m2b_orchestration as workflow_contract


class PublicEvidenceRedactionTests(unittest.TestCase):
    def test_original_release_gate_with_posix_temp_path(self):
        case = workflow_contract.M2BContractTests(
            "test_35_secret_values_are_redacted_from_public_evidence")
        case.setUp()
        try:
            # Exercise the unchanged failing CI assertion on any local OS.
            case.root = PurePosixPath("/tmp/cek-redaction-fixture")
            case.test_35_secret_values_are_redacted_from_public_evidence()
        finally:
            case.doCleanups()

    def test_windows_posix_unc_and_file_uri_in_error_text(self):
        for path in ("/tmp/fixture/private.txt", "/home/fixture/project/a.py",
                     r"C:\Users\fixture\private.txt", "C:/Users/fixture/private.txt",
                     r"\\server\share\private.txt", "//server/share/private.txt",
                     "file:///home/fixture/private.txt"):
            with self.subTest(path=path):
                self.assertEqual(_sanitize_text("Cannot open " + path + "; denied"),
                                 "Cannot open <private-path>; denied")

    def test_quoted_paths_with_spaces_preserve_diagnostic_text(self):
        for path in ("/home/Fixture User/project/a.py", r"C:\Users\Fixture User\a.py",
                     "/home/O'Connor/private file.py"):
            with self.subTest(path=path):
                self.assertEqual(_sanitize_text('File "' + path + '", line 7: denied'),
                                 'File "<private-path>", line 7: denied')
        self.assertEqual(_sanitize_text("Cannot open '/home/Fixture User/a.py': denied"),
                         "Cannot open '<private-path>': denied")

    def test_nested_paths_and_errors_are_sanitized_without_mutating_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = WorkflowLedger(Path(directory) / "ledger.json")
            ledger.append_raw({"error": {"code": "EACCES", "message": "denied: /home/fixture/a.py",
                                        "worktreeRoot": "  /home/Fixture User/project",
                                        "details": [{"cwd": "/home/Fixture User/project"},
                                                    {"filePath": r"C:\Fixture User\a.py"},
                                                    {"paths": ["/home/Fixture User/a.py", "/"]}]},
                               "url": "https://example.invalid/docs/api", "artifact": "src/module.py"})
            before = ledger.path.read_bytes()
            original = json.dumps(ledger.events, sort_keys=True)
            evidence = ledger.sanitized_export()["events"][-1]["evidence"]
            text = json.dumps(evidence)
            self.assertNotIn("fixture/a.py", text)
            self.assertNotIn("Fixture User", text)
            self.assertEqual(evidence["error"]["code"], "EACCES")
            self.assertEqual(evidence["error"]["worktreeRoot"], "<private-path>")
            self.assertEqual(evidence["error"]["details"][-1]["paths"], ["<private-path>"] * 2)
            self.assertEqual(evidence["url"], "https://example.invalid/docs/api")
            self.assertEqual(evidence["artifact"], "src/module.py")
            self.assertEqual(before, ledger.path.read_bytes())
            self.assertEqual(original, json.dumps(ledger.events, sort_keys=True))

    def test_path_dictionary_keys_remain_distinct_without_exposing_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = WorkflowLedger(Path(directory) / "ledger.json")
            ledger.append_raw({"errors": {"/home/Fixture User/one.py": "FIRST",
                                          "/home/Fixture User/two.py": "SECOND"}})
            errors = ledger.sanitized_export()["events"][-1]["evidence"]["errors"]
            self.assertEqual(set(errors.values()), {"FIRST", "SECOND"})
            self.assertEqual(len(errors), 2)
            self.assertNotIn("Fixture User", json.dumps(errors))

    def test_public_urls_relative_paths_and_status_are_preserved(self):
        for text in ("https://example.invalid/a/b?x=1", "See https://example.invalid/a/b for help",
                     "src/module.py", "./src/module.py", "feature/reliability", "PASS: 133/133",
                     "git@github.com:owner/repo.git", "GET https://example.invalid/api/v1"):
            with self.subTest(text=text):
                self.assertEqual(_sanitize_text(text), text)


if __name__ == "__main__":
    unittest.main()
