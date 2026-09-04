from __future__ import annotations

import json
import re
import unittest
from dataclasses import replace
from pathlib import Path

from benchmarks.model import load_cases, load_configurations, planned_attempt_count
from benchmarks.report import BenchmarkRun, TokenEvidence, build_report, load_run_records, report_record

ROOT = Path(__file__).resolve().parents[1]
FIXTURES_ROOT = ROOT / "benchmarks" / "fixtures"
FIXTURE_COMMIT = "1dbf382b6e838ca351c6fb8818a64aa793176198"

EXPECTED_FIXTURES = {
    "node-small-bug",
    "backend-design",
    "frontend-review",
    "concurrency-pressure",
    "repository-review",
}
EXPECTED_STRATEGIES = {
    "A": "naive-always-loaded",
    "B": "progressive-disclosure",
    "C": "isolated-subagent",
}
EXPECTED_SKILLS = {
    "node-small-bug": None,
    "backend-design": "backend-patterns",
    "frontend-review": "frontend-patterns",
    "concurrency-pressure": "concurrency-performance",
    "repository-review": "orchestrator",
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
        directories = {path.name for path in FIXTURES_ROOT.iterdir() if path.is_dir()}
        self.assertEqual(directories - {"results"}, EXPECTED_FIXTURES)
        self.assertTrue(directories <= EXPECTED_FIXTURES | {"results"})

    def test_each_fixture_contains_source_and_no_forbidden_content(self) -> None:
        for fixture_id in sorted(EXPECTED_FIXTURES):
            fixture = FIXTURES_ROOT / fixture_id
            self.assertTrue(fixture.is_dir(), f"missing fixture: {fixture_id}")
            paths = list(fixture.rglob("*"))
            self.assertTrue(
                any(path.is_file() and path.suffix.lower() in SOURCE_SUFFIXES for path in paths),
                f"fixture has no source file: {fixture_id}",
            )
            for path in paths:
                if path.is_dir():
                    self.assertNotIn(path.name, GENERATED_DIRS)
                    continue
                text = path.read_text(encoding="utf-8")
                self.assertNotRegex(text, r"\b(?:TODO|TBD)\b")
                for pattern in SECRET_PATTERNS + ABSOLUTE_USER_PATHS:
                    self.assertIsNone(pattern.search(text), f"forbidden content in {path.relative_to(ROOT)}")


class BenchmarkProtocolTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configurations = load_configurations(ROOT / "benchmarks" / "configurations")
        self.cases = load_cases(ROOT / "benchmarks" / "cases")

    def test_configuration_protocol_is_exact(self) -> None:
        self.assertEqual({item.id: item.strategy for item in self.configurations}, EXPECTED_STRATEGIES)
        self.assertTrue(all(item.instruction.strip() for item in self.configurations))

    def test_case_protocol_is_exact_and_pinned(self) -> None:
        self.assertEqual({item.id for item in self.cases}, EXPECTED_FIXTURES)
        for item in self.cases:
            self.assertEqual(item.fixture, item.id)
            self.assertRegex(item.repository_commit, r"^[0-9a-f]{40}$")
            self.assertEqual(item.repository_commit, FIXTURE_COMMIT)
            self.assertTrue(item.prompt.strip())
            self.assertGreaterEqual(len(item.invariants), 2)
            self.assertEqual(item.required_skill, EXPECTED_SKILLS[item.id])

    def test_complete_campaign_requires_three_repetitions(self) -> None:
        self.assertEqual(planned_attempt_count(self.cases, self.configurations, 3), 45)
        with self.assertRaises(ValueError):
            planned_attempt_count(self.cases, self.configurations, 2)


class BenchmarkReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.configurations = load_configurations(ROOT / "benchmarks" / "configurations")
        self.cases = load_cases(ROOT / "benchmarks" / "cases")
        self.runs = load_run_records(
            ROOT / "benchmarks" / "fixtures" / "results" / "complete-synthetic.json"
        )

    def test_complete_campaign_requires_exact_coverage_and_runtime_identity(self) -> None:
        report = build_report(self.runs, self.cases, self.configurations, 3)
        self.assertEqual(report.expected_runs, 45)
        self.assertEqual(report.observed_runs, 45)
        self.assertTrue(report.complete)

        skewed = (replace(self.runs[0], model="different-model"),) + self.runs[1:]
        skew_report = build_report(skewed, self.cases, self.configurations, 3)
        self.assertFalse(skew_report.complete)
        self.assertTrue(any("runtime identity mismatch" in item for item in skew_report.blockers))

    def test_missing_and_duplicate_tuples_are_blockers(self) -> None:
        incomplete = build_report(self.runs[:-1], self.cases, self.configurations, 3)
        self.assertFalse(incomplete.complete)
        self.assertEqual(incomplete.observed_runs, 44)
        self.assertTrue(any("missing run tuple" in item for item in incomplete.blockers))

        duplicate = build_report(self.runs + (self.runs[0],), self.cases, self.configurations, 3)
        self.assertFalse(duplicate.complete)
        self.assertEqual(duplicate.observed_runs, 46)
        self.assertTrue(any("duplicate run tuple" in item for item in duplicate.blockers))

    def test_invalid_sources_and_negative_counts_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TokenEvidence(1, "invented")
        with self.assertRaises(ValueError):
            TokenEvidence(-1, "measured")
        with self.assertRaises(ValueError):
            replace(self.runs[0], duration_ms=-1)
        with self.assertRaises(ValueError):
            replace(self.runs[0], tool_calls=-1)

    def test_aggregation_uses_median_range_and_separate_sources(self) -> None:
        runs = list(self.runs)
        indexes = [
            i for i, run in enumerate(runs)
            if run.case_id == "backend-design" and run.configuration_id == "A"
        ]
        for index, value in zip(indexes, (100, 120, 500)):
            runs[index] = replace(runs[index], input_tokens=TokenEvidence(value, "measured"))
        report = build_report(tuple(runs), self.cases, self.configurations, 3)
        group = next(
            item for item in report.aggregates
            if item["caseId"] == "backend-design"
            and item["configurationId"] == "A"
            and item["metric"] == "inputTokens"
            and item["source"] == "measured"
        )
        self.assertEqual(
            (group["median"], group["min"], group["max"], group["n"]),
            (120, 100, 500, 3),
        )

        runs[indexes[-1]] = replace(
            runs[indexes[-1]], input_tokens=TokenEvidence(500, "estimated")
        )
        split = build_report(tuple(runs), self.cases, self.configurations, 3)
        groups = [
            item for item in split.aggregates
            if item["caseId"] == "backend-design"
            and item["configurationId"] == "A"
            and item["metric"] == "inputTokens"
        ]
        self.assertEqual({item["source"] for item in groups}, {"measured", "estimated"})
        self.assertEqual(sorted(item["n"] for item in groups), [1, 2])

    def test_report_contains_no_forbidden_claims(self) -> None:
        record = report_record(build_report(self.runs, self.cases, self.configurations, 3))
        serialized = json.dumps(record, sort_keys=True).casefold()
        for forbidden in ("statistically significant", "pass@k", "pass^k", '"lean":true'):
            self.assertNotIn(forbidden, serialized)


class PlanEStaticContractTests(unittest.TestCase):
    def test_benchmark_documentation_contract(self) -> None:
        path = ROOT / "docs" / "benchmark.md"
        self.assertTrue(path.is_file(), "missing docs/benchmark.md")
        text = path.read_text(encoding="utf-8")
        for phrase in (
            "A = naive always-loaded engineering instructions",
            "B = progressive-disclosure skill routing",
            "C = native isolated subagent delegation",
            "5 tasks × 3 configurations × 3 repeats = 45 runs",
            "median and range",
            "measured",
            "exported",
            "estimated",
            "no statistical significance claim from three repeats",
        ):
            self.assertIn(phrase, text)
        lowered = text.casefold()
        self.assertIn("synthetic", lowered)
        self.assertIn("do not earn a `lean` claim", lowered)
        self.assertIn(FIXTURE_COMMIT, text)

    def test_plan_e_ci_matrix_and_commands_are_exact(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("  plan-e-contracts:", workflow)
        plan_e = workflow.split("  plan-e-contracts:", 1)[1]
        self.assertIn("os: [ubuntu-latest, windows-latest, macos-latest]", plan_e)
        self.assertIn("python-version: '3.11'", plan_e)
        for command in (
            "python -m unittest tests.test_worktree_acceptance -v",
            "python -m unittest tests.test_domain_skills -v",
            "python -m unittest tests.test_benchmark_contract -v",
            "python tests/validate_content.py",
            "python -m benchmarks.cli validate --cases benchmarks/cases --configurations benchmarks/configurations",
        ):
            self.assertIn(command, plan_e)
        self.assertNotIn("codex exec", plan_e)
        self.assertNotIn("codex_pressure", plan_e)


if __name__ == "__main__":
    unittest.main()
