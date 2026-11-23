"""Frozen benchmark protocol vs separate patched dependency candidate."""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from benchmarks.model import load_cases


ROOT = Path(__file__).resolve().parents[1]
LEGACY = ROOT / "benchmarks" / "fixtures" / "frontend-review"
CANDIDATE = ROOT / "benchmarks" / "candidates" / "frontend-review-v2"
PIN = "1dbf382b6e838ca351c6fb8818a64aa793176198"


class PatchedFrontendCandidateTests(unittest.TestCase):
    def test_legacy_fixture_and_protocol_are_untouched(self) -> None:
        original = json.loads((LEGACY / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(original["dependencies"]["next"], "15.0.0")
        self.assertEqual(original["dependencies"]["react"], "19.0.0")
        cases = load_cases(ROOT / "benchmarks" / "cases")
        self.assertEqual(len(cases), 5)
        self.assertEqual({case.repository_commit for case in cases}, {PIN})
        self.assertEqual(next(case for case in cases if case.id == "frontend-review").fixture, "frontend-review")
        self.assertNotIn("frontend-review-v2", {case.id for case in cases})

    def test_candidate_keeps_intentional_review_page_verbatim(self) -> None:
        self.assertEqual(
            (CANDIDATE / "app" / "page.tsx").read_bytes(),
            (LEGACY / "app" / "page.tsx").read_bytes(),
        )
        self.assertTrue((CANDIDATE / "app" / "layout.tsx").is_file())
        self.assertTrue((CANDIDATE / "README.md").is_file())

    def test_new_dependency_versions_are_exact_and_frozen_in_lock(self) -> None:
        package = json.loads((CANDIDATE / "package.json").read_text(encoding="utf-8"))
        lock = json.loads((CANDIDATE / "package-lock.json").read_text(encoding="utf-8"))
        self.assertTrue(package["private"])
        self.assertEqual(package["dependencies"]["next"], "16.4.5")
        self.assertEqual(package["dependencies"]["react"], "19.3.1")
        self.assertEqual(package["dependencies"]["react-dom"], "19.3.1")
        self.assertEqual(lock["lockfileVersion"], 3)
        self.assertEqual(lock["packages"][""]["dependencies"], package["dependencies"])
        self.assertEqual(lock["packages"]["node_modules/next"]["version"], "16.4.5")
        self.assertEqual(lock["packages"]["node_modules/react"]["version"], "19.3.1")
        self.assertEqual(lock["packages"]["node_modules/react-dom"]["version"], "19.3.1")
        self.assertEqual(package["devDependencies"]["@types/node"], "22.15.30")
        self.assertEqual(lock["packages"]["node_modules/@types/node"]["version"], "22.15.30")
        self.assertEqual(lock["packages"][""]["devDependencies"], package["devDependencies"])
        tsconfig = json.loads((CANDIDATE / "tsconfig.json").read_text(encoding="utf-8"))
        self.assertEqual(tsconfig["compilerOptions"]["jsx"], "react-jsx")
        self.assertIn(".next/dev/types/**/*.ts", tsconfig["include"])
        self.assertTrue(
            all(not version.startswith(("^", "~", ">", "<", "*")) for version in package["dependencies"].values())
        )

    def test_candidate_is_not_an_ordinary_active_fixture(self) -> None:
        # It must not be accidentally included in existing 45-run plan.
        self.assertFalse((ROOT / "benchmarks" / "cases" / "frontend-review-v2.json").exists())
        self.assertFalse((ROOT / "benchmarks" / "fixtures" / "frontend-review-v2").exists())
        self.assertFalse((CANDIDATE / "node_modules").exists())


if __name__ == "__main__":
    unittest.main()
