from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from scripts.cek_lifecycle import LifecycleError, install, main, uninstall, update, verify, verify_clean


class FakeCodex:
    def __init__(self, *, version: str = "codex-cli 0.153.0", marketplace_root: str | None = None):
        self.version = version
        self.marketplace_root = marketplace_root
        self.plugin_installed = False
        self.plugin_version = "1.0.0"
        self.plugin_marketplace_name = "codex-engineering-kit-dev"
        self.marketplace_remove_leaves_entry = False
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], env: dict[str, str]) -> dict[str, object]:
        self.calls.append(args)
        if args == ["--version"]:
            return {"returncode": 0, "stdout": self.version, "stderr": ""}
        if args == ["plugin", "marketplace", "list", "--json"]:
            marketplaces = (
                [{"name": "codex-engineering-kit-dev", "root": self.marketplace_root}]
                if self.marketplace_root is not None
                else []
            )
            return {"returncode": 0, "stdout": json.dumps({"marketplaces": marketplaces}), "stderr": ""}
        if len(args) == 5 and args[:3] == ["plugin", "marketplace", "add"] and args[-1] == "--json":
            self.marketplace_root = args[3]
            return {
                "returncode": 0,
                "stdout": json.dumps({"marketplaceName": "codex-engineering-kit-dev"}),
                "stderr": "",
            }
        if args == ["plugin", "marketplace", "remove", "codex-engineering-kit-dev", "--json"]:
            if not self.marketplace_remove_leaves_entry:
                self.marketplace_root = None
            return {"returncode": 0, "stdout": "{}", "stderr": ""}
        if args == ["plugin", "list", "--json"]:
            installed = []
            if self.plugin_installed:
                installed.append(
                    {
                        "name": "codex-engineering-kit",
                        "marketplaceName": self.plugin_marketplace_name,
                        "version": self.plugin_version,
                        "installed": True,
                        "enabled": True,
                    }
                )
            return {
                "returncode": 0,
                "stdout": json.dumps({"installed": installed, "available": []}),
                "stderr": "",
            }
        if args == ["plugin", "add", "codex-engineering-kit@codex-engineering-kit-dev", "--json"]:
            self.plugin_installed = True
            installed_path = (
                Path(env["CODEX_HOME"])
                / "plugins"
                / "cache"
                / "codex-engineering-kit-dev"
                / "codex-engineering-kit"
                / self.plugin_version
            )
            if installed_path.exists():
                shutil.rmtree(installed_path)
            shutil.copytree(Path(self.marketplace_root), installed_path)
            return {
                "returncode": 0,
                "stdout": json.dumps(
                    {
                        "name": "codex-engineering-kit",
                        "marketplaceName": "codex-engineering-kit-dev",
                        "version": self.plugin_version,
                        "installedPath": str(installed_path),
                    }
                ),
                "stderr": "",
            }
        if args == ["plugin", "remove", "codex-engineering-kit@codex-engineering-kit-dev", "--json"]:
            self.plugin_installed = False
            return {"returncode": 0, "stdout": "{}", "stderr": ""}
        return {"returncode": 2, "stdout": "", "stderr": f"unexpected command: {args}"}


class CleanInstallLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="cek-clean-install-test-")
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
        self._write_source("1.0.0", "reviewer-v1")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _write_source(self, version: str, reviewer: str) -> None:
        (self.repo / ".codex-plugin" / "plugin.json").write_text(
            json.dumps({"name": "codex-engineering-kit", "version": version}),
            encoding="utf-8",
        )
        (self.repo / ".agents" / "plugins" / "marketplace.json").write_text(
            json.dumps(
                {
                    "name": "codex-engineering-kit-dev",
                    "plugins": [
                        {
                            "name": "codex-engineering-kit",
                            "source": {"source": "local", "path": "."},
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.repo / ".codex" / "agents" / "reviewer.toml").write_text(
            reviewer,
            encoding="utf-8",
        )
        (self.repo / "hooks" / "hooks.json").write_text('{"hooks": {}}', encoding="utf-8")
        (self.repo / "skills" / "example" / "SKILL.md").write_text("example", encoding="utf-8")

    def test_clean_install_update_uninstall_and_reinstall(self) -> None:
        codex = FakeCodex()
        project_sentinel = self.project / "user-owned.txt"
        home_sentinel = self.home / "user-owned.txt"
        project_sentinel.write_text("keep project", encoding="utf-8")
        self.home.mkdir()
        home_sentinel.write_text("keep home", encoding="utf-8")

        installed = install(self.repo, self.project, self.home, codex)
        self.assertEqual(installed["status"], "installed")
        self.assertEqual(
            (self.project / ".codex" / "agents" / "reviewer.toml").read_text(encoding="utf-8"),
            "reviewer-v1",
        )
        self.assertEqual(verify(self.repo, self.project, self.home, codex)["status"], "verified")

        self._write_source("1.0.1", "reviewer-v2")
        codex.plugin_version = "1.0.1"
        updated = update(self.repo, self.project, self.home, codex)
        self.assertEqual(updated["fromVersion"], "1.0.0")
        self.assertEqual(updated["toVersion"], "1.0.1")
        self.assertEqual(verify(self.repo, self.project, self.home, codex)["status"], "verified")

        removed = uninstall(self.repo, self.project, self.home, codex)
        self.assertEqual(removed["status"], "uninstalled")
        self.assertEqual(verify_clean(self.repo, self.project, self.home, codex)["status"], "clean")
        self.assertTrue(project_sentinel.is_file())
        self.assertTrue(home_sentinel.is_file())
        self.assertFalse((self.project / ".codex" / "agents" / "reviewer.toml").exists())

        self.assertEqual(install(self.repo, self.project, self.home, codex)["status"], "installed")
        self.assertEqual(verify(self.repo, self.project, self.home, codex)["status"], "verified")

    def test_install_refuses_unowned_reviewer_before_cli_mutation(self) -> None:
        target = self.project / ".codex" / "agents" / "reviewer.toml"
        target.parent.mkdir(parents=True)
        target.write_text("user-owned", encoding="utf-8")
        codex = FakeCodex()

        with self.assertRaisesRegex(LifecycleError, "unowned project-local reviewer"):
            install(self.repo, self.project, self.home, codex)

        self.assertEqual(codex.calls, [["--version"]])
        self.assertEqual(target.read_text(encoding="utf-8"), "user-owned")

    def test_verify_rejects_tampered_packaged_hook(self) -> None:
        codex = FakeCodex()
        install(self.repo, self.project, self.home, codex)
        installed_path = (
            self.home
            / "plugins"
            / "cache"
            / "codex-engineering-kit-dev"
            / "codex-engineering-kit"
            / "1.0.0"
        )
        (installed_path / "hooks" / "hooks.json").write_text("tampered", encoding="utf-8")

        with self.assertRaisesRegex(LifecycleError, "packaged plugin asset"):
            verify(self.repo, self.project, self.home, codex)

    def test_documented_cli_dispatches_install(self) -> None:
        codex = FakeCodex()
        with patch(
            "scripts.cek_lifecycle.run_codex",
            side_effect=lambda _executable, args, env: codex(args, env),
        ):
            exit_code = main(
                [
                    "install",
                    "--repo",
                    str(self.repo),
                    "--project",
                    str(self.project),
                    "--codex-home",
                    str(self.home),
                    "--codex",
                    "fake-codex",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertTrue((self.project / ".codex" / "agents" / "reviewer.toml").is_file())

    def test_update_refuses_modified_owned_reviewer(self) -> None:
        codex = FakeCodex()
        install(self.repo, self.project, self.home, codex)
        target = self.project / ".codex" / "agents" / "reviewer.toml"
        target.write_text("user change", encoding="utf-8")
        before = list(codex.calls)

        with self.assertRaisesRegex(LifecycleError, "modified project-local reviewer"):
            update(self.repo, self.project, self.home, codex)

        self.assertEqual(codex.calls, before + [["--version"]])
        self.assertEqual(target.read_text(encoding="utf-8"), "user change")

    def test_update_refuses_same_name_plugin_from_another_marketplace(self) -> None:
        codex = FakeCodex()
        install(self.repo, self.project, self.home, codex)
        codex.plugin_marketplace_name = "other-marketplace"
        before = list(codex.calls)

        with self.assertRaisesRegex(LifecycleError, "different marketplace"):
            update(self.repo, self.project, self.home, codex)

        self.assertEqual(codex.calls, before + [["--version"], ["plugin", "marketplace", "list", "--json"], ["plugin", "list", "--json"]])

    def test_uninstall_preserves_modified_reviewer_and_unrelated_files(self) -> None:
        codex = FakeCodex()
        install(self.repo, self.project, self.home, codex)
        target = self.project / ".codex" / "agents" / "reviewer.toml"
        target.write_text("user change", encoding="utf-8")
        unrelated = self.project / ".codex" / "agents" / "user-agent.toml"
        unrelated.write_text("keep", encoding="utf-8")

        result = uninstall(self.repo, self.project, self.home, codex)

        self.assertEqual(result["preserved"], [".codex/agents/reviewer.toml"])
        self.assertEqual(target.read_text(encoding="utf-8"), "user change")
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")
        self.assertFalse((self.project / ".codex" / "codex-engineering-kit.install.json").exists())

    def test_preexisting_marketplace_survives_managed_uninstall(self) -> None:
        codex = FakeCodex(marketplace_root=str(self.repo.resolve()))

        install(self.repo, self.project, self.home, codex)
        uninstall(self.repo, self.project, self.home, codex)

        self.assertEqual(codex.marketplace_root, str(self.repo.resolve()))
        self.assertNotIn(
            ["plugin", "marketplace", "remove", "codex-engineering-kit-dev", "--json"],
            codex.calls,
        )

    def test_uninstall_refuses_marketplace_rebinding_before_mutation(self) -> None:
        codex = FakeCodex()
        install(self.repo, self.project, self.home, codex)
        codex.marketplace_root = str((self.root / "different-repo").resolve())
        before = list(codex.calls)

        with self.assertRaisesRegex(LifecycleError, "different local root"):
            uninstall(self.repo, self.project, self.home, codex)

        self.assertEqual(codex.calls, before + [["--version"], ["plugin", "marketplace", "list", "--json"]])
        self.assertTrue((self.home / "codex-engineering-kit.install.json").is_file())

    def test_verify_clean_refuses_a_surviving_cek_marketplace(self) -> None:
        codex = FakeCodex()
        install(self.repo, self.project, self.home, codex)
        codex.marketplace_remove_leaves_entry = True

        with self.assertRaisesRegex(LifecycleError, "marketplace removal was not confirmed"):
            uninstall(self.repo, self.project, self.home, codex)

        with self.assertRaisesRegex(LifecycleError, "managed lifecycle state remains"):
            verify_clean(self.repo, self.project, self.home, codex)

    def test_install_refuses_marketplace_name_bound_to_another_checkout(self) -> None:
        codex = FakeCodex(marketplace_root=str((self.root / "different-repo").resolve()))

        with self.assertRaisesRegex(LifecycleError, "different local root"):
            install(self.repo, self.project, self.home, codex)

        self.assertFalse(codex.plugin_installed)
        self.assertFalse((self.project / ".codex").exists())

    def test_unsupported_cli_fails_before_any_write(self) -> None:
        codex = FakeCodex(version="codex-cli 0.154.0")

        with self.assertRaisesRegex(LifecycleError, "requires Codex CLI 0.153.0"):
            install(self.repo, self.project, self.home, codex)

        self.assertFalse(self.home.exists())
        self.assertFalse((self.project / ".codex").exists())
        self.assertEqual(codex.calls, [["--version"]])


if __name__ == "__main__":
    unittest.main()
