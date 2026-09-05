from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from statistics import median

from benchmarks.model import BenchmarkCase, BenchmarkConfiguration, planned_attempt_count

_TOKEN_SOURCES = {"measured", "exported", "estimated", "unavailable"}
_RUN_STATUSES = {"PASS", "FAIL", "UNAVAILABLE"}


@dataclass(frozen=True)
class TokenEvidence:
    value: int | None
    source: str

    def __post_init__(self) -> None:
        if self.source not in _TOKEN_SOURCES:
            raise ValueError(f"invalid token evidence source: {self.source}")
        if self.source == "unavailable":
            if self.value is not None:
                raise ValueError("unavailable token evidence must have value=None")
            return
        if not isinstance(self.value, int) or isinstance(self.value, bool) or self.value < 0:
            raise ValueError(f"{self.source} token evidence requires a non-negative integer value")


@dataclass(frozen=True)
class BenchmarkRun:
    case_id: str
    configuration_id: str
    repeat: int
    status: str
    model: str
    reasoning: str
    codex_version: str
    input_tokens: TokenEvidence
    output_tokens: TokenEvidence
    cached_input_tokens: TokenEvidence
    duration_ms: int
    tool_calls: int | None
    parent_context_tokens: TokenEvidence | None
    subagent_tokens: TokenEvidence | None

    def __post_init__(self) -> None:
        if not self.case_id or not self.configuration_id:
            raise ValueError("benchmark run requires case and configuration ids")
        if not isinstance(self.repeat, int) or isinstance(self.repeat, bool) or self.repeat < 1:
            raise ValueError("benchmark repeat must be a positive integer")
        if self.status not in _RUN_STATUSES:
            raise ValueError(f"invalid benchmark run status: {self.status}")
        if not self.model.strip() or not self.reasoning.strip() or not self.codex_version.strip():
            raise ValueError("benchmark run requires model, reasoning, and Codex version")
        if not isinstance(self.duration_ms, int) or isinstance(self.duration_ms, bool) or self.duration_ms < 0:
            raise ValueError("duration_ms must be a non-negative integer")
        if self.tool_calls is not None and (
            not isinstance(self.tool_calls, int)
            or isinstance(self.tool_calls, bool)
            or self.tool_calls < 0
        ):
            raise ValueError("tool_calls must be None or a non-negative integer")


@dataclass(frozen=True)
class BenchmarkReport:
    schema_version: int
    kind: str
    complete: bool
    expected_runs: int
    observed_runs: int
    blockers: tuple[str, ...]
    aggregates: tuple[dict[str, object], ...]


def _token_evidence(record: object, field: str) -> TokenEvidence:
    if not isinstance(record, dict):
        raise ValueError(f"{field} must be a token evidence object")
    return TokenEvidence(record.get("value"), record.get("source"))


def _optional_token_evidence(record: object, field: str) -> TokenEvidence | None:
    if record is None:
        return None
    return _token_evidence(record, field)


def load_run_records(path: Path) -> tuple[BenchmarkRun, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("runs"), list):
        raise ValueError("benchmark run file must contain a top-level runs array")
    runs: list[BenchmarkRun] = []
    for record in payload["runs"]:
        if not isinstance(record, dict):
            raise ValueError("benchmark run record must be an object")
        runs.append(
            BenchmarkRun(
                case_id=record.get("caseId"),
                configuration_id=record.get("configurationId"),
                repeat=record.get("repeat"),
                status=record.get("status"),
                model=record.get("model"),
                reasoning=record.get("reasoning"),
                codex_version=record.get("codexVersion"),
                input_tokens=_token_evidence(record.get("inputTokens"), "inputTokens"),
                output_tokens=_token_evidence(record.get("outputTokens"), "outputTokens"),
                cached_input_tokens=_token_evidence(record.get("cachedInputTokens"), "cachedInputTokens"),
                duration_ms=record.get("durationMs"),
                tool_calls=record.get("toolCalls"),
                parent_context_tokens=_optional_token_evidence(
                    record.get("parentContextTokens"), "parentContextTokens"
                ),
                subagent_tokens=_optional_token_evidence(
                    record.get("subagentTokens"), "subagentTokens"
                ),
            )
        )
    return tuple(runs)


def _add_numeric(
    groups: dict[tuple[str, str, str, str], list[int]],
    run: BenchmarkRun,
    metric: str,
    source: str,
    value: int | None,
) -> None:
    if value is None:
        return
    groups.setdefault((run.case_id, run.configuration_id, metric, source), []).append(value)


def build_report(
    runs: tuple[BenchmarkRun, ...],
    cases: tuple[BenchmarkCase, ...],
    configurations: tuple[BenchmarkConfiguration, ...],
    repetitions: int = 3,
) -> BenchmarkReport:
    expected_runs = planned_attempt_count(cases, configurations, repetitions)
    expected_tuples = {
        (case.id, configuration.id, repeat)
        for case in cases
        for configuration in configurations
        for repeat in range(1, repetitions + 1)
    }

    tuple_counts: dict[tuple[str, str, int], int] = {}
    blockers: list[str] = []
    for run in runs:
        key = (run.case_id, run.configuration_id, run.repeat)
        tuple_counts[key] = tuple_counts.get(key, 0) + 1

    for key in sorted(expected_tuples):
        count = tuple_counts.get(key, 0)
        if count == 0:
            blockers.append(f"missing run tuple: {key[0]}/{key[1]}/{key[2]}")
        elif count > 1:
            blockers.append(f"duplicate run tuple: {key[0]}/{key[1]}/{key[2]} count={count}")

    for key in sorted(set(tuple_counts) - expected_tuples):
        blockers.append(f"unexpected run tuple: {key[0]}/{key[1]}/{key[2]}")

    runtime_identities = {(run.model, run.reasoning, run.codex_version) for run in runs}
    if len(runtime_identities) > 1:
        blockers.append("runtime identity mismatch across campaign")

    status_counts: dict[tuple[str, str], dict[str, int]] = {}
    groups: dict[tuple[str, str, str, str], list[int]] = {}

    for run in runs:
        status = status_counts.setdefault(
            (run.case_id, run.configuration_id),
            {"PASS": 0, "FAIL": 0, "UNAVAILABLE": 0},
        )
        status[run.status] += 1

        for metric, evidence in (
            ("inputTokens", run.input_tokens),
            ("outputTokens", run.output_tokens),
            ("cachedInputTokens", run.cached_input_tokens),
            ("parentContextTokens", run.parent_context_tokens),
            ("subagentTokens", run.subagent_tokens),
        ):
            if evidence is not None:
                _add_numeric(groups, run, metric, evidence.source, evidence.value)

        _add_numeric(groups, run, "durationMs", "measured", run.duration_ms)
        _add_numeric(groups, run, "toolCalls", "measured", run.tool_calls)

    aggregates: list[dict[str, object]] = []
    for (case_id, configuration_id, metric, source), values in sorted(groups.items()):
        counts = status_counts[(case_id, configuration_id)]
        aggregates.append(
            {
                "caseId": case_id,
                "configurationId": configuration_id,
                "metric": metric,
                "source": source,
                "median": median(values),
                "min": min(values),
                "max": max(values),
                "n": len(values),
                "passCount": counts["PASS"],
                "failCount": counts["FAIL"],
                "unavailableCount": counts["UNAVAILABLE"],
            }
        )

    complete = len(runs) == expected_runs and not blockers and set(tuple_counts) == expected_tuples
    return BenchmarkReport(
        schema_version=1,
        kind="context-benchmark-report",
        complete=complete,
        expected_runs=expected_runs,
        observed_runs=len(runs),
        blockers=tuple(blockers),
        aggregates=tuple(aggregates),
    )


def report_record(report: BenchmarkReport) -> dict[str, object]:
    return {
        "schemaVersion": report.schema_version,
        "kind": report.kind,
        "complete": report.complete,
        "expectedRuns": report.expected_runs,
        "observedRuns": report.observed_runs,
        "blockers": list(report.blockers),
        "aggregates": list(report.aggregates),
    }
