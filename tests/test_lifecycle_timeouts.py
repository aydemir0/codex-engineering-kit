"""Bounded native Codex lifecycle operations; no real Codex/auth required."""
from __future__ import annotations

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from scripts.cek_lifecycle import (
    DEFAULT_CODEX_TIMEOUT_SECONDS,
    GLOBAL_STATE_NAME,
    PROJECT_ASSET,
    PROJECT_STATE,
    LifecycleError,
    _codex_phase,
    _parser,
    install,
    main,
    run_codex,
    verify,
)
from tests.test_clean_install_lifecycle import FakeCodex


def make_disposable_cli(
    folder: Path,
    *,
    spawn_grandchild: bool = False,
    hang_args: tuple[str, ...] = ("plugin", "list", "--json"),
) -> Path:
    """Make an entirely local fake Codex executable (not a real runtime)."""
    python = folder / "slow_codex.py"
    script = [
        "import pathlib, subprocess, sys, time",
        f"if sys.argv[1:] != {list(hang_args)!r}:",
        "    sys.exit(4)",
    ]
    if spawn_grandchild:
        spawned = repr(str(folder / "child-spawned"))
        marker = repr(str(folder / "child-survived"))
        code = (
            "import pathlib,time;"
            f"pathlib.Path({spawned}).write_text('started');"
            "time.sleep(2);"
            f"pathlib.Path({marker}).write_text('survived')"
        )
        script.append(f"subprocess.Popen([sys.executable, '-c', {code!r}])")
        script.append("time.sleep(60)")
    else:
        script.append("time.sleep(60)")
    python.write_text("\n".join(script) + "\n", encoding="utf-8")
    if os.name == "nt":
        launcher = folder / "slow-codex.cmd"
        launcher.write_text(
            f'@echo off\n"{sys.executable}" "{python}" %*\n', encoding="utf-8"
        )
    else:
        launcher = folder / "slow-codex"
        launcher.write_text(
            f"#!{sys.executable}\n" + python.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        launcher.chmod(0o700)
    return launcher


class LifecycleTimeoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cek-timeout-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.project = self.root / "project"
        self.home = self.root / "codex-home"
        (self.repo / ".codex-plugin").mkdir(parents=True)
        (self.repo / ".agents" / "plugins").mkdir(parents=True)
        (self.repo / ".codex" / "agents").mkdir(parents=True)
        (self.repo / "hooks").mkdir()
        (self.repo / "skills" / "example").mkdir(parents=True)
        self.project.mkdir()
        (self.repo / ".codex-plugin" / "plugin.json").write_text(
            '{"name":"codex-engineering-kit","version":"1.0.0"}',
            encoding="utf-8",
        )
        (self.repo / ".agents" / "plugins" / "marketplace.json").write_text(
            json.dumps({
                "name": "codex-engineering-kit-dev",
                "plugins": [{
                    "name": "codex-engineering-kit",
                    "source": {"source": "local", "path": "."},
                }],
            }),
            encoding="utf-8",
        )
        (self.repo / ".codex" / "agents" / "reviewer.toml").write_text(
            "reviewer fixture", encoding="utf-8"
        )
        (self.repo / "hooks" / "hooks.json").write_text(
            '{"hooks":{}}', encoding="utf-8"
        )
        (self.repo / "skills" / "example" / "SKILL.md").write_text(
            "fixture", encoding="utf-8"
        )

    def test_default_and_configured_timeout_is_bounded(self) -> None:
        self.assertEqual(DEFAULT_CODEX_TIMEOUT_SECONDS, 120)
        self.assertEqual(_parser().parse_args([
            "verify", "--project", str(self.project),
            "--codex-timeout-seconds", "0.25",
        ]).codex_timeout_seconds, 0.25)
        for value in ("0", "-4", "nan", "inf", "901", "invalid"):
            with self.subTest(value=value), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    _parser().parse_args([
                        "verify", "--project", str(self.project),
                        "--codex-timeout-seconds", value,
                    ])
        with self.assertRaisesRegex(LifecycleError, "timeout"):
            run_codex(sys.executable, ["--version"], os.environ, timeout_seconds=0)

    def test_phase_name_never_prints_plugin_identity_or_args(self) -> None:
        self.assertEqual(_codex_phase(["--version"]), "runtime version")
        self.assertEqual(_codex_phase(["plugin", "marketplace", "list", "--json"]), "marketplace list")
        self.assertEqual(_codex_phase(["plugin", "list", "--json"]), "plugin list")
        self.assertEqual(_codex_phase(["plugin", "add", "sensitive-identity", "--json"]), "plugin add")
        self.assertNotIn("sensitive-identity", _codex_phase(["plugin", "add", "sensitive-identity", "--json"]))

    def test_delayed_subprocess_fails_in_bounded_time(self) -> None:
        launcher = make_disposable_cli(self.root)
        environment = dict(os.environ)
        secret = "sk-" + "T" * 30  # synthetic marker, never a real API key
        environment["CEK_SYNTHETIC_SECRET"] = secret
        start = time.monotonic()
        with self.assertRaisesRegex(LifecycleError, r"CODEX_CLI_TIMEOUT: phase=plugin list; limit=0\.4s") as caught:
            run_codex(str(launcher), ["plugin", "list", "--json"], environment, timeout_seconds=0.4)
        elapsed = time.monotonic() - start
        self.assertLess(elapsed, 11)
        self.assertIn("retry verify", str(caught.exception))
        self.assertNotIn(str(self.root), str(caught.exception))
        self.assertNotIn(secret, str(caught.exception))

    def test_timeout_returns_when_a_surviving_child_keeps_output_open(self) -> None:
        ready = self.root / "child-started"
        child = f"from pathlib import Path; import time; Path({str(ready)!r}).touch(); time.sleep(6)"
        parent = (
            "import subprocess, sys, time\n"
            f"subprocess.Popen([sys.executable, '-c', {child!r}])\n"
            "time.sleep(6)\n"
        )
        if os.name == "nt":
            cleanup_denied = patch("scripts.cek_lifecycle._windows_taskkill", return_value=None)
        else:
            cleanup_denied = patch("scripts.cek_lifecycle.os.killpg", side_effect=PermissionError)

        start = time.monotonic()
        with cleanup_denied, self.assertRaisesRegex(LifecycleError, "CODEX_CLI_TIMEOUT"):
            run_codex(sys.executable, ["-c", parent], os.environ, timeout_seconds=0.8)
        elapsed = time.monotonic() - start

        self.assertTrue(ready.exists(), "the descendant must have inherited the output handles")
        self.assertLess(elapsed, 3, "cleanup must not wait for a descendant to close its output")

    def test_run_codex_preserves_exit_code_and_utf8_output(self) -> None:
        script = (
            "import sys; "
            "sys.stdout.buffer.write(b'caf\\xc3\\xa9\\r\\nsecond line\\r\\n'); "
            "sys.stderr.buffer.write(b'diagnostic\\r\\n'); "
            "sys.exit(7)"
        )
        result = run_codex(sys.executable, ["-c", script], os.environ)
        self.assertEqual(result, {
            "returncode": 7,
            "stdout": "caf\u00e9\nsecond line",
            "stderr": "diagnostic",
        })

    def test_verify_plugin_list_timeout_preserves_managed_and_user_state(self) -> None:
        codex = FakeCodex()
        project_user = self.project / "user-owned.txt"
        project_user.write_bytes(b"preserve project")
        self.home.mkdir()
        home_user = self.home / "user-owned.txt"
        home_user.write_bytes(b"preserve home")
        self.assertEqual(install(self.repo, self.project, self.home, codex)["status"], "installed")
        tracked = (
            self.home / GLOBAL_STATE_NAME,
            self.project / PROJECT_STATE,
            self.project / PROJECT_ASSET,
            home_user,
            project_user,
        )
        originals = {path: path.read_bytes() for path in tracked}
        launcher = make_disposable_cli(self.root)

        def runner(args: list[str], env: dict[str, str]) -> dict[str, object]:
            if args == ["plugin", "list", "--json"]:
                return run_codex(str(launcher), args, env, timeout_seconds=0.45)
            return codex(args, env)

        start = time.monotonic()
        with self.assertRaisesRegex(LifecycleError, "phase=plugin list"):
            verify(self.repo, self.project, self.home, runner)
        self.assertLess(time.monotonic() - start, 11)
        self.assertEqual({p: p.read_bytes() for p in tracked}, originals)
        self.assertTrue(codex.plugin_installed)

    def test_install_plugin_list_timeout_does_not_write_manifests(self) -> None:
        fake = FakeCodex()
        sentinel = self.project / "keep.txt"
        sentinel.write_bytes(b"keep")
        launcher = make_disposable_cli(self.root)

        def runner(args: list[str], env: dict[str, str]) -> dict[str, object]:
            if args == ["plugin", "list", "--json"]:
                return run_codex(str(launcher), args, env, timeout_seconds=0.4)
            return fake(args, env)

        with self.assertRaisesRegex(LifecycleError, "phase=plugin list"):
            install(self.repo, self.project, self.home, runner)
        self.assertFalse((self.home / GLOBAL_STATE_NAME).exists())
        self.assertFalse((self.project / PROJECT_STATE).exists())
        self.assertFalse((self.project / PROJECT_ASSET).exists())
        self.assertEqual(sentinel.read_bytes(), b"keep")
        self.assertFalse(fake.plugin_installed)

    def test_install_plugin_add_timeout_preserves_uncertain_marketplace(self) -> None:
        fake = FakeCodex()
        command = [
            "plugin", "add", "codex-engineering-kit@codex-engineering-kit-dev", "--json"
        ]
        launcher = make_disposable_cli(self.root, hang_args=tuple(command))
        sentinel = self.project / "keep.txt"
        sentinel.write_bytes(b"foreign state")

        def runner(args: list[str], env: dict[str, str]) -> dict[str, object]:
            if args == command:
                return run_codex(str(launcher), args, env, timeout_seconds=0.4)
            return fake(args, env)

        with self.assertRaisesRegex(LifecycleError, r"CODEX_CLI_TIMEOUT: phase=plugin add"):
            install(self.repo, self.project, self.home, runner)
        # After an uncertain external mutation, do not attempt automatic
        # marketplace removal: Codex may have partially installed the plugin.
        self.assertEqual(fake.marketplace_root, str(self.repo.resolve()))
        self.assertNotIn(
            ["plugin", "marketplace", "remove", "codex-engineering-kit-dev", "--json"],
            fake.calls,
        )
        self.assertFalse((self.home / GLOBAL_STATE_NAME).exists())
        self.assertFalse((self.project / PROJECT_STATE).exists())
        self.assertFalse((self.project / PROJECT_ASSET).exists())
        self.assertEqual(sentinel.read_bytes(), b"foreign state")

    def test_cli_forwards_configured_timeout_to_native_runner(self) -> None:
        fake = FakeCodex()
        captured: list[float] = []

        def fake_run(executable, command, env, timeout_seconds=120):
            captured.append(timeout_seconds)
            return fake(command, env)

        with (
            patch("scripts.cek_lifecycle.require_complete_package"),
            patch("scripts.cek_lifecycle.require_native_host", return_value={}),
            patch("scripts.cek_lifecycle.run_codex", side_effect=fake_run),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            result = main([
                "install", "--repo", str(self.repo),
                "--project", str(self.project),
                "--codex-home", str(self.home),
                "--codex", "fixture-codex",
                "--codex-timeout-seconds", "0.5",
            ])
        self.assertEqual(result, 0)
        self.assertTrue(captured)
        self.assertTrue(all(value == 0.5 for value in captured))

    def test_documentation_explains_frozen_beta_and_timeout_recovery(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        install_docs = (repo / "docs" / "install.md").read_text(encoding="utf-8")
        quickstart = (repo / "docs" / "quickstart.md").read_text(encoding="utf-8")
        for phrase in (
            "--codex-timeout-seconds",
            "CODEX_CLI_TIMEOUT",
            "plugin list",
            "v1.1.0-beta.1",
            "does **not** include this",
        ):
            self.assertIn(phrase, install_docs)
        self.assertIn("already enumerates plugins", quickstart)
        self.assertIn("predates post-beta timeout hardening", quickstart)

    def test_timeout_kills_descendant_not_just_parent(self) -> None:
        launcher = make_disposable_cli(self.root, spawn_grandchild=True)
        with self.assertRaisesRegex(LifecycleError, "CODEX_CLI_TIMEOUT"):
            run_codex(str(launcher), ["plugin", "list", "--json"], os.environ, timeout_seconds=0.8)
        spawned = self.root / "child-spawned"
        self.assertTrue(spawned.exists(), "fixture must actually start a grandchild")
        time.sleep(2.4)
        self.assertFalse((self.root / "child-survived").exists(), "child of timed-out CLI must be terminated")


if __name__ == "__main__":
    unittest.main()
