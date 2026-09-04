from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = ROOT / "benchmarks" / "fixtures"

EXPECTED_FIXTURES = {
    "node-small-bug",
    "backend-design",
    "frontend-review",
    "concurrency-pressure",
    "repository-review",
}

SOURCE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx"}
GENERATED_DIRS = {"node_modules", "__pycache__", ".next", "dist", "build"}
SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"ghp_[A-Za-z0-9]{16,}"),
    re.compile(r"BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
)
ABSOLUTE_USER_PATHS = (
    re.compile(r"(?i)[A-Z]:\\Users\\"),
    re.compile(r"/Users/"),
    re.compile(r"/home/[^/\s]+/"),
)


class BenchmarkFixtureTests(unittest.TestCase):
    def test_fixture_inventory_is_exact_and_static(self) -> None:
        self.assertTrue(FIXTURES_ROOT.is_dir(), "missing benchmarks/fixtures")
        actual = {path.name for path in FIXTURES_ROOT.iterdir() if path.is_dir()}
        self.assertEqual(actual, EXPECTED_FIXTURES)

    def test_each_fixture_contains_source_and_no_forbidden_content(self) -> None:
        self.assertTrue(FIXTURES_ROOT.is_dir(), "missing benchmarks/fixtures")
        for fixture_id in sorted(EXPECTED_FIXTURES):
            fixture = FIXTURES_ROOT / fixture_id
            self.assertTrue(fixture.is_dir(), f"missing fixture: {fixture_id}")
            all_files = [path for path in fixture.rglob("*") if path.is_file()]
            source_files = [path for path in all_files if path.suffix.lower() in SOURCE_SUFFIXES]
            self.assertTrue(source_files, f"fixture has no source file: {fixture_id}")
            for path in fixture.rglob("*"):
                if path.is_dir():
                    self.assertNotIn(
                        path.name,
                        GENERATED_DIRS,
                        f"generated dependency directory in {fixture_id}: {path.name}",
                    )
                    continue
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"\b(?:TODO|TBD)\b", f"placeholder in {path.relative_to(ROOT)}")
                for pattern in SECRET_PATTERNS:
                    self.assertIsNone(pattern.search(text), f"secret-like token in {path.relative_to(ROOT)}")
                for pattern in ABSOLUTE_USER_PATHS:
                    self.assertIsNone(pattern.search(text), f"absolute user path in {path.relative_to(ROOT)}")


if __name__ == "__main__":
    unittest.main()
