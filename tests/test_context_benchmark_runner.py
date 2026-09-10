from __future__ import annotations

import json
import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

from benchmarks.model import load_cases, load_configurations
from benchmarks.report import build_report, load_run_records
from scripts.acceptance.context_benchmark import (
    RETRY_POLICY,
    build_attempt_prompt,
    planned_attempts,
    run_context_benchmark,
    validate_campaign_file,
)


ROOT = Path(__file__).resolve().parents[1]
FAKE_CODEX = r'''
from __future__ import annotations
import json
import os
import re
import sys

args = sys.argv[1:]
if args == ["--version"]:
    print("codex-cli 0.153.0-test")
    raise SystemExit(0)
if args == ["exec", "--help"]:
    print("Usage: codex exec --json --ephemeral --ignore-user-config --ignore-rules --sandbox read-only --model MODEL --output-schema FILE")
    raise SystemExit(0)

prompt = sys.stdin.read() if args[-1] == "-" else args[-1]
case_id = re.search(r"Benchmark case: ([a-z-]+)", prompt).group(1)
configuration_id = re.search(r"Benchmark configuration: ([ABC])", prompt).group(1)
failing = os.environ.get("CEK_FAKE_FAIL_TUPLE")
repeat = os.environ.get("CEK_BENCHMARK_REPEAT", "")
if failing == f"{case_id}/{configuration_id}/{repeat}":
    print("synthetic failure", file=sys.stderr)
    raise SystemExit(7)

answers = {
    "node-small-bug": ["src/range.ts rangeInclusive uses current < end, an inclusive boundary defect"],
    "backend-design": ["api.py provider.charge lacks idempotency and crosses commit transaction failure boundaries"],
    "frontend-review": ["app/page.tsx is a use client component; clickable div needs keyboard and button accessibility"],
    "concurrency-pressure": ["worker.py asyncio.gather is unbounded; add a semaphore and measure latency throughput"],
    "repository-review": ["service.py retries inside one transaction while storage.py commits and swallows DatabaseError as False"],
}
response = json.dumps({"findings": [{"claim": answers[case_id][0], "evidence": answers[case_id]}], "verification": ["fixture inspection"]})
print(json.dumps({"type": "thread.started", "thread_id": "private-session-id"}))
if configuration_id == "C":
    print(json.dumps({"type": "item.completed", "item": {"type": "collaboration_tool_call", "tool": "spawn_agent", "status": "completed", "agent_type": "explorer"}}))
print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": response}}))
print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 101, "cached_input_tokens": 7, "output_tokens": 23}}))
print("sk-THIS_VALUE_STAYS_ONLY_IN_LOCAL_RAW C:\\Users\\private-user sessionId=private", file=sys.stderr)
'''


class ContextBenchmarkRunnerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fake = self.root / "fake_codex.py"
        self.fake.write_text(FAKE_CODEX, encoding="utf-8")
        self.output = self.root / "runs.json"
        self.raw = self.root / "raw"
        self.cases = load_cases(ROOT / "benchmarks" / "cases")
        self.configurations = load_configurations(ROOT / "benchmarks" / "configurations")
        self.commit = "78206e1a67800f21f059c7c699727fc3d40df9cf"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_campaign(self, *, smoke: bool = False, environment: dict[str, str] | None = None) -> dict:
        return run_context_benchmark(
            codex_command=(sys.executable, str(self.fake)),
            repo_path=ROOT,
            case_dir=ROOT / "benchmarks" / "cases",
            configuration_dir=ROOT / "benchmarks" / "configurations",
            fixture_root=ROOT / "benchmarks" / "fixtures",
            skill_root=ROOT / "skills",
            explorer_agent=ROOT / ".codex" / "agents" / "explorer.toml",
            output_path=self.output,
            raw_dir=self.raw,
            cek_commit=self.commit,
            campaign_id="unit-test-campaign",
            model="test-model",
            reasoning="medium",
            timeout_seconds=5,
            smoke=smoke,
            environment=environment,
        )

    def test_attempt_plan_is_exact_unique_and_deterministic(self) -> None:
        attempts = planned_attempts(self.cases, self.configurations, 3)
        keys = [(case.id, config.id, repeat) for case, config, repeat in attempts]
        self.assertEqual(len(keys), 45)
        self.assertEqual(len(set(keys)), 45)
        self.assertEqual(keys, sorted(keys))

    def test_script_entrypoint_loads_from_repository_root(self) -> None:
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / "acceptance" / "context_benchmark.py"), "--help"],
            cwd=str(self.root),
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("authenticated CEK context benchmark", completed.stdout)

    def test_prompt_context_differs_only_by_declared_mode(self) -> None:
        case = next(item for item in self.cases if item.id == "backend-design")
        by_id = {item.id: item for item in self.configurations}
        prompt_a = build_attempt_prompt(case, by_id["A"], ROOT / "skills")
        prompt_b = build_attempt_prompt(case, by_id["B"], ROOT / "skills")
        prompt_c = build_attempt_prompt(case, by_id["C"], ROOT / "skills")

        self.assertIn("name: backend-patterns", prompt_a)
        self.assertIn("name: frontend-patterns", prompt_a)
        self.assertIn("name: backend-patterns", prompt_b)
        self.assertNotIn("name: frontend-patterns", prompt_b)
        self.assertNotIn("name: backend-patterns", prompt_c)
        self.assertIn("spawn the project-local explorer", prompt_c)

    def test_smoke_is_one_non_counted_attempt(self) -> None:
        record = self.run_campaign(smoke=True)
        self.assertEqual(record["kind"], "authenticated-context-benchmark-smoke")
        self.assertFalse(record["counted"])
        self.assertEqual(len(record["runs"]), 1)
        self.assertEqual(list(self.raw.glob("*.jsonl")).__len__(), 1)

    def test_full_campaign_writes_45_loader_compatible_measured_rows(self) -> None:
        record = self.run_campaign()
        runs = load_run_records(self.output)
        report = build_report(runs, self.cases, self.configurations, 3)

        self.assertEqual(record["retryPolicy"], RETRY_POLICY)
        self.assertEqual(record["cekCommit"], self.commit)
        self.assertEqual(len(record["runs"]), 45)
        self.assertEqual(len(list(self.raw.glob("*.jsonl"))), 45)
        self.assertTrue(report.complete)
        self.assertTrue(all(run.input_tokens.source == "measured" for run in runs))
        self.assertTrue(all(run.output_tokens.source == "measured" for run in runs))
        self.assertTrue(all(item["qualityPassed"] for item in record["runs"]))
        self.assertTrue(all(item["subagentLifecycle"] for item in record["runs"] if item["configurationId"] == "C"))

        payload = json.loads(self.output.read_text(encoding="utf-8"))
        payload["candidateStable"] = True
        self.output.write_text(json.dumps(payload), encoding="utf-8")
        validated = validate_campaign_file(
            self.output,
            ROOT / "benchmarks" / "cases",
            ROOT / "benchmarks" / "configurations",
            expected_commit=self.commit,
            expected_methodology=record["methodologySha256"],
        )
        self.assertTrue(validated.complete)

    def test_validator_rejects_unstable_or_incomplete_campaign(self) -> None:
        record = self.run_campaign()
        payload = json.loads(self.output.read_text(encoding="utf-8"))
        payload["candidateStable"] = False
        self.output.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "candidate was not stable"):
            validate_campaign_file(
                self.output,
                ROOT / "benchmarks" / "cases",
                ROOT / "benchmarks" / "configurations",
                expected_commit=self.commit,
                expected_methodology=record["methodologySha256"],
            )

    def test_failure_is_retained_once_without_selective_retry(self) -> None:
        env = os.environ.copy()
        env["CEK_FAKE_FAIL_TUPLE"] = "backend-design/B/2"
        record = self.run_campaign(environment=env)
        failed = [item for item in record["runs"] if item["status"] == "FAIL"]

        self.assertEqual(len(record["runs"]), 45)
        self.assertEqual(len(failed), 1)
        self.assertEqual(
            (failed[0]["caseId"], failed[0]["configurationId"], failed[0]["repeat"]),
            ("backend-design", "B", 2),
        )
        self.assertEqual(failed[0]["failureKind"], "nonzero-exit")

    def test_sanitized_dataset_keeps_only_hashes_of_raw_capture(self) -> None:
        record = self.run_campaign(smoke=True)
        serialized = json.dumps(record, sort_keys=True)
        self.assertNotIn("private-session-id", serialized)
        self.assertNotIn("private-user", serialized)
        self.assertNotIn("sk-THIS_VALUE", serialized)
        self.assertRegex(record["runs"][0]["captureSha256"], r"^[0-9a-f]{64}$")


if __name__ == "__main__":
    unittest.main()
