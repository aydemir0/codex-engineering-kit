"""Runtime identity contract tests; fake binaries never execute."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from runtime.assurance import native_host
from scripts import cek_lifecycle


ROOT = Path(__file__).resolve().parents[1]


class RuntimeCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.exe = self.root / "codex.exe"
        self.host = self.root / "codex-code-mode-host.exe"
        self.exe.write_bytes(b"synthetic CLI identity fixture")
        self.host.write_bytes(b"synthetic host identity fixture")
        self.cli_sha = hashlib.sha256(self.exe.read_bytes()).hexdigest()
        self.host_sha = hashlib.sha256(self.host.read_bytes()).hexdigest()

    def version(self, text="codex-cli 0.155.1", code=0):
        return subprocess.CompletedProcess([], code, text.encode(), b"")

    def test_documented_runtime_matches_native_and_installer_policy(self):
        self.assertEqual(cek_lifecycle.SUPPORTED_RUNTIME, "codex-cli 0.155.1")
        self.assertEqual(native_host.RUNTIME_VERSION, "0.155.1")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        install = (ROOT / "docs/install.md").read_text(encoding="utf-8")
        self.assertIn("requires Python 3.11+ and exactly Codex CLI 0.155.1", readme)
        self.assertIn("supports exactly Codex CLI 0.155.1", install)
        for text in (readme, install):
            for line in text.splitlines():
                if line.startswith("python scripts/cek_lifecycle.py "):
                    self.assertIn("--codex <runtime>/bin/codex.exe", line)
        current = json.loads((ROOT / "release_contracts/compatibility.json").read_text(encoding="utf-8"))["currentProductRuntime"]
        self.assertEqual(current["cliVersion"], native_host.RUNTIME_VERSION)
        self.assertEqual(native_host.HOSTS[current["cliSHA256"]], current["hostSHA256"])
        self.assertEqual(current["modelDrivenWorkflow"], "NOT_RUN")
        self.assertIn(current["packageSHA256"], install)
        self.assertIn(current["packageUrl"], install)

    def test_identity_and_version_bind_before_real_host_probe(self):
        with patch.dict(native_host.HOSTS, {self.cli_sha: self.host_sha}, clear=True), \
             patch.object(native_host.subprocess, "run", return_value=self.version()) as version, \
             patch.object(native_host, "probe_host", return_value={"toolInvocation": "PASS"}) as probe:
            result = native_host.require_native_host(self.exe)
        self.assertEqual(result["runtimeVersion"], "0.155.1")
        self.assertEqual(result["runtimeSHA256"], self.cli_sha)
        self.assertEqual(version.call_args.args[0], [str(self.exe), "--version"])
        self.assertEqual(probe.call_args.kwargs["expected_sha256"], self.host_sha)
        self.assertNotIn("OPENAI_API_KEY", version.call_args.kwargs["env"])

    def test_version_disagreement_fails_before_host_execution(self):
        for banner, code in (("codex-cli 0.153.0", 0), ("codex-cli 0.155.1", 1), ("", 0)):
            with self.subTest(banner=banner, code=code), \
                 patch.dict(native_host.HOSTS, {self.cli_sha: self.host_sha}, clear=True), \
                 patch.object(native_host.subprocess, "run", return_value=self.version(banner, code)), \
                 patch.object(native_host, "probe_host") as probe:
                with self.assertRaises(native_host.NativeHostError):
                    native_host.require_native_host(self.exe)
                probe.assert_not_called()

    def test_unsupported_or_modified_binary_never_executes(self):
        with patch.dict(native_host.HOSTS, {}, clear=True), \
             patch.object(native_host.subprocess, "run") as version, \
             patch.object(native_host, "probe_host") as probe:
            with self.assertRaisesRegex(native_host.NativeHostError, "CODE_MODE_RUNTIME_UNSUPPORTED"):
                native_host.require_native_host(self.exe)
            version.assert_not_called()
            probe.assert_not_called()

    def test_modified_host_fails_without_starting_host(self):
        self.host.write_bytes(b"modified fixture host")
        with patch.dict(native_host.HOSTS, {self.cli_sha: self.host_sha}, clear=True), \
             patch.object(native_host.subprocess, "run", return_value=self.version()), \
             patch.object(native_host.subprocess, "Popen") as start:
            with self.assertRaisesRegex(native_host.NativeHostError, "CODE_MODE_HOST_DIGEST"):
                native_host.require_native_host(self.exe)
            start.assert_not_called()

    def test_missing_or_incomplete_package_fails_closed(self):
        self.host.unlink()
        with patch.object(native_host.subprocess, "run") as version:
            with self.assertRaisesRegex(native_host.NativeHostError, "CODE_MODE_HOST_MISSING"):
                native_host.require_native_host(self.exe)
            version.assert_not_called()

    def test_version_timeout_is_structured_and_blocks_host(self):
        with patch.dict(native_host.HOSTS, {self.cli_sha: self.host_sha}, clear=True), \
             patch.object(native_host.subprocess, "run", side_effect=subprocess.TimeoutExpired("fixture", 1)), \
             patch.object(native_host, "probe_host") as probe:
            with self.assertRaises(native_host.NativeHostError):
                native_host.require_native_host(self.exe)
            probe.assert_not_called()

    def test_cli_install_rejects_bad_identity_before_any_profile_write(self):
        (self.root / "project").mkdir()
        with patch("scripts.cek_lifecycle.require_complete_package"), \
             patch("scripts.cek_lifecycle.require_native_host", create=True,
                   side_effect=native_host.NativeHostError("CODE_MODE_RUNTIME_UNSUPPORTED")) as guard, \
             patch("scripts.cek_lifecycle.run_codex") as command:
            code = cek_lifecycle.main(["install", "--project", str(self.root / "project"),
                                      "--codex-home", str(self.root / "profile"), "--codex", str(self.exe)])
            self.assertEqual(code, 1)
            guard.assert_called_once()
            command.assert_not_called()
        self.assertFalse((self.root / "profile").exists())

    def test_complete_package_requires_every_approved_file(self):
        exe = self.root / "package/bin/codex.exe"
        expected = {}
        for name in native_host.PACKAGE_FILES:
            path = exe.parent.parent / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(name.encode())
            expected[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        with patch.dict(native_host.PACKAGE_FILES, expected, clear=True):
            native_host.require_complete_package(exe)
            resource = exe.parent.parent / "codex-resources/codex-command-runner.exe"
            original = resource.read_bytes()
            resource.unlink()
            with self.assertRaises(native_host.NativeHostError):
                native_host.require_complete_package(exe)
            resource.write_bytes(original + b"altered")
            with self.assertRaisesRegex(native_host.NativeHostError, "PACKAGE_DIGEST"):
                native_host.require_complete_package(exe)

    def test_launcher_is_not_a_verified_native_package(self):
        with self.assertRaisesRegex(native_host.NativeHostError, "COMPLETE_PACKAGE_REQUIRED"):
            native_host.require_complete_package(self.root / "codex.cmd")


if __name__ == "__main__":
    unittest.main()
