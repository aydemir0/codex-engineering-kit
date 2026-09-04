from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from verification.package_manager import detect_package_manager, package_script_command


class PackageManagerResolutionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_package_json(self, payload: dict | None = None) -> None:
        data = {"name": "cek-fixture", "private": True}
        if payload:
            data.update(payload)
        (self.root / "package.json").write_text(
            json.dumps(data),
            encoding="utf-8",
        )

    @staticmethod
    def which_with(*available: str):
        available_set = set(available)

        def resolve(name: str) -> str | None:
            return f"/fake/bin/{name}" if name in available_set else None

        return resolve

    def test_explicit_manager_beats_package_manager_and_lockfile(self) -> None:
        self.write_package_json({"packageManager": "yarn@4.6.0"})
        (self.root / "bun.lock").write_text("", encoding="utf-8")

        selected = detect_package_manager(
            self.root,
            explicit="pnpm",
            which=self.which_with("pnpm", "yarn", "bun", "npm"),
        )

        self.assertEqual((selected.name, selected.source), ("pnpm", "explicit"))
        self.assertIsNone(selected.detail)

    def test_package_manager_field_beats_lockfile_and_parses_version(self) -> None:
        self.write_package_json({"packageManager": "yarn@4.6.0"})
        (self.root / "pnpm-lock.yaml").write_text("", encoding="utf-8")

        selected = detect_package_manager(
            self.root,
            which=self.which_with("yarn", "pnpm", "npm"),
        )

        self.assertEqual((selected.name, selected.source), ("yarn", "packageManager"))
        self.assertIsNone(selected.detail)

    def test_bun_package_manager_field_is_supported(self) -> None:
        self.write_package_json({"packageManager": "bun@1.2.3"})

        selected = detect_package_manager(
            self.root,
            which=self.which_with("bun", "npm"),
        )

        self.assertEqual((selected.name, selected.source), ("bun", "packageManager"))

    def test_single_lockfile_selects_its_manager(self) -> None:
        self.write_package_json()
        (self.root / "pnpm-lock.yaml").write_text("", encoding="utf-8")

        selected = detect_package_manager(
            self.root,
            which=self.which_with("pnpm", "npm"),
        )

        self.assertEqual((selected.name, selected.source), ("pnpm", "lockfile"))
        self.assertIsNone(selected.detail)

    def test_conflicting_manager_lockfiles_are_ambiguous(self) -> None:
        self.write_package_json()
        (self.root / "pnpm-lock.yaml").write_text("", encoding="utf-8")
        (self.root / "yarn.lock").write_text("", encoding="utf-8")

        selected = detect_package_manager(
            self.root,
            which=self.which_with("pnpm", "yarn", "npm"),
        )

        self.assertIsNone(selected.name)
        self.assertEqual(selected.source, "lockfile")
        self.assertEqual(selected.detail, "ambiguous-lockfiles")

    def test_available_non_npm_fallback_prefers_pnpm_then_yarn_then_bun(self) -> None:
        self.write_package_json()

        selected = detect_package_manager(
            self.root,
            which=self.which_with("pnpm", "yarn", "bun", "npm"),
        )
        self.assertEqual((selected.name, selected.source), ("pnpm", "available"))

        selected = detect_package_manager(
            self.root,
            which=self.which_with("yarn", "bun", "npm"),
        )
        self.assertEqual((selected.name, selected.source), ("yarn", "available"))

        selected = detect_package_manager(
            self.root,
            which=self.which_with("bun", "npm"),
        )
        self.assertEqual((selected.name, selected.source), ("bun", "available"))

    def test_npm_fallback_requires_package_json_and_available_npm(self) -> None:
        without_package = detect_package_manager(
            self.root,
            which=self.which_with("npm"),
        )
        self.assertIsNone(without_package.name)
        self.assertEqual(without_package.detail, "not-a-node-project")

        self.write_package_json()
        with_package = detect_package_manager(
            self.root,
            which=self.which_with("npm"),
        )
        self.assertEqual((with_package.name, with_package.source), ("npm", "fallback"))

    def test_authoritative_supported_manager_missing_is_not_replaced_by_npm(self) -> None:
        self.write_package_json({"packageManager": "yarn@4.6.0"})

        selected = detect_package_manager(
            self.root,
            which=self.which_with("npm"),
        )

        self.assertEqual(selected.name, "yarn")
        self.assertEqual(selected.source, "packageManager")
        self.assertEqual(selected.detail, "unavailable")

    def test_unsupported_authoritative_manager_is_reported_without_npm_fallback(self) -> None:
        self.write_package_json({"packageManager": "deno@2.0.0"})

        selected = detect_package_manager(
            self.root,
            which=self.which_with("npm"),
        )

        self.assertIsNone(selected.name)
        self.assertEqual(selected.source, "packageManager")
        self.assertEqual(selected.detail, "unsupported-manager:deno")

    def test_script_command_rendering_is_manager_specific(self) -> None:
        self.assertEqual(
            package_script_command("npm", "test"),
            ["npm", "run", "test", "--silent"],
        )
        self.assertEqual(
            package_script_command("pnpm", "test"),
            ["pnpm", "run", "test", "--silent"],
        )
        self.assertEqual(
            package_script_command("yarn", "test"),
            ["yarn", "run", "test", "--silent"],
        )
        self.assertEqual(
            package_script_command("bun", "test"),
            ["bun", "run", "test"],
        )


if __name__ == "__main__":
    unittest.main()
