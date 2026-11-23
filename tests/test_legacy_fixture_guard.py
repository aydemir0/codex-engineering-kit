"""Negative tests for the deprecated historical frontend fixture execution boundary."""
from __future__ import annotations

import tempfile
import subprocess
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from benchmarks.model import load_cases, load_configurations
from scripts.acceptance.context_benchmark import (
    LEGACY_UNSAFE_MESSAGE,
    LEGACY_ARCHIVED_MANIFEST,
    LEGACY_ORIGINAL_MANIFEST,
    _verify_fixture_pins,
    _reject_deprecated_fixture_cases,
    _run_attempt,
    run_context_benchmark,
)

ROOT = Path(__file__).resolve().parents[1]


class LegacyFixtureGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.cases = load_cases(ROOT / "benchmarks" / "cases")
        self.configurations = load_configurations(ROOT / "benchmarks" / "configurations")
        self.legacy = next(case for case in self.cases if case.fixture == "frontend-review")

    def test_legacy_manifest_is_non_installable_and_archived_exactly(self) -> None:
        self.assertFalse((ROOT / LEGACY_ORIGINAL_MANIFEST).exists())
        archived = ROOT / LEGACY_ARCHIVED_MANIFEST
        self.assertTrue(archived.is_file())
        original = subprocess.check_output(
            ["git", "show", f"{self.legacy.repository_commit}:{LEGACY_ORIGINAL_MANIFEST}"],
            cwd=ROOT,
        )
        self.assertEqual(archived.read_bytes().replace(b"\r\n", b"\n"), original)
        self.assertIn(b'"next": "15.0.0"', original)

    def test_fixture_provenance_still_checks_historical_git_blob(self) -> None:
        self.assertEqual(
            _verify_fixture_pins(ROOT, ROOT / "benchmarks" / "fixtures", self.cases),
            self.legacy.repository_commit,
        )

    def test_archive_integrity_check_rejects_corrupted_bytes(self) -> None:
        original_read = Path.read_bytes
        archived_path = ROOT / LEGACY_ARCHIVED_MANIFEST

        def corrupt_only_archive(path: Path) -> bytes:
            if path == archived_path:
                return b'{"name":"tampered"}\n'
            return original_read(path)

        with patch.object(Path, "read_bytes", corrupt_only_archive):
            with self.assertRaisesRegex(ValueError, "manifest archive is missing or modified"):
                _verify_fixture_pins(ROOT, ROOT / "benchmarks" / "fixtures", self.cases)

    def test_legacy_fixture_is_rejected_even_when_case_id_is_renamed(self) -> None:
        renamed = replace(self.legacy, id="renamed-unsafe-case")
        with self.assertRaisesRegex(ValueError, "disabled for new benchmark execution"):
            _reject_deprecated_fixture_cases((renamed,))

    def test_safe_case_is_not_blocked(self) -> None:
        safe = next(case for case in self.cases if case.fixture == "node-small-bug")
        _reject_deprecated_fixture_cases((safe,))

    def test_full_campaign_denied_before_codex_probe_or_artifact_creation(self) -> None:
        output = self.work / "campaign.json"
        raw = self.work / "raw"
        with patch(
            "scripts.acceptance.context_benchmark._probe",
            side_effect=AssertionError("Codex must not be probed"),
        ), patch(
            "scripts.acceptance.context_benchmark._run_attempt",
            side_effect=AssertionError("No benchmark attempt may execute"),
        ):
            with self.assertRaisesRegex(ValueError, "historical frontend-review"):
                run_context_benchmark(
                    codex_command=("not-a-real-codex",),
                    repo_path=ROOT,
                    case_dir=ROOT / "benchmarks" / "cases",
                    configuration_dir=ROOT / "benchmarks" / "configurations",
                    fixture_root=ROOT / "benchmarks" / "fixtures",
                    skill_root=ROOT / "skills",
                    explorer_agent=ROOT / ".codex" / "agents" / "explorer.toml",
                    hook_manifest=ROOT / "hooks" / "hooks.json",
                    hook_dispatcher=ROOT / "hooks" / "scripts" / "hook_dispatch.py",
                    output_path=output,
                    raw_dir=raw,
                    cek_commit="0" * 40,
                    campaign_id="guard-negative",
                    model="no-model",
                    reasoning="medium",
                    timeout_seconds=1,
                )
        self.assertFalse(output.exists())
        self.assertFalse(raw.exists())

    def test_direct_attempt_denied_before_fixture_copy_or_process(self) -> None:
        with patch(
            "scripts.acceptance.context_benchmark.shutil.copytree",
            side_effect=AssertionError("Fixture must not be copied"),
        ), patch(
            "scripts.acceptance.context_benchmark._run",
            side_effect=AssertionError("Process must not execute"),
        ):
            with self.assertRaisesRegex(ValueError, "disabled for new benchmark execution"):
                _run_attempt(
                    ordinal=1,
                    case=self.legacy,
                    configuration=self.configurations[0],
                    repeat=1,
                    codex_command=("no-codex",),
                    codex_version="irrelevant",
                    fixture_root=ROOT / "benchmarks" / "fixtures",
                    skill_root=ROOT / "skills",
                    explorer_agent=ROOT / ".codex" / "agents" / "explorer.toml",
                    raw_dir=self.work / "raw",
                    model="no-model",
                    reasoning="medium",
                    timeout_seconds=1,
                    environment={},
                )
        self.assertFalse((self.work / "raw").exists())

    def test_security_message_has_no_override_instructions(self) -> None:
        self.assertIn("unresolved vulnerable dependencies", LEGACY_UNSAFE_MESSAGE)
        self.assertNotIn("override", LEGACY_UNSAFE_MESSAGE.lower())


if __name__ == "__main__":
    unittest.main()
