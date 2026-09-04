from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from evals.grader import grade_candidate
from evals.model import load_cases
from runtime.state import write_state

SCHEMA_VERSION = 1
CAMPAIGN_KIND = "eval-campaign"
DEFAULT_ARTIFACT = Path(".codex-kit") / "evals" / "offline" / "latest.json"
MAX_REASON_BYTES = 8192


@dataclass(frozen=True)
class EvalCaseRun:
    case_id: str
    case_class: str
    grader_type: str
    attempts: int
    result: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class EvalCampaignResult:
    schema_version: int
    mode: str
    cases: tuple[EvalCaseRun, ...]
    attempt_count: int
    blocking_failures: tuple[str, ...]
    status: str


def _bounded(text: str) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= MAX_REASON_BYTES:
        return text
    return encoded[:MAX_REASON_BYTES].decode("utf-8", errors="ignore")


def _case_record(case: EvalCaseRun) -> dict:
    return {
        "id": case.case_id,
        "class": case.case_class,
        "graderType": case.grader_type,
        "attempts": case.attempts,
        "result": case.result,
        "reasons": list(case.reasons),
    }


def campaign_record(result: EvalCampaignResult) -> dict:
    return {
        "schemaVersion": result.schema_version,
        "kind": CAMPAIGN_KIND,
        "mode": result.mode,
        "attemptCount": result.attempt_count,
        "cases": [_case_record(case) for case in result.cases],
        "blockingFailures": list(result.blocking_failures),
        "status": result.status,
    }


def _write_campaign(result: EvalCampaignResult) -> None:
    full = campaign_record(result)
    payload = {key: value for key, value in full.items() if key not in {"schemaVersion", "kind"}}
    write_state(DEFAULT_ARTIFACT, CAMPAIGN_KIND, payload)


def run_offline_campaign(case_dir: Path | str, fixture_dir: Path | str) -> EvalCampaignResult:
    case_dir = Path(case_dir)
    fixture_dir = Path(fixture_dir)

    case_runs: list[EvalCaseRun] = []
    blockers: list[str] = []
    attempt_count = 0

    for case in load_cases(case_dir):
        fixture_path = fixture_dir / f"{case.id}.safe.json"
        if not fixture_path.is_file():
            reason = _bounded(f"{case.id}: safe offline fixture unavailable")
            case_runs.append(
                EvalCaseRun(
                    case_id=case.id,
                    case_class=case.case_class,
                    grader_type=case.grader_type,
                    attempts=0,
                    result="UNAVAILABLE",
                    reasons=(reason,),
                )
            )
            blockers.append(reason)
            continue

        try:
            candidate = json.loads(fixture_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            reason = _bounded(f"{case.id}: offline fixture unreadable: {type(exc).__name__}")
            case_runs.append(
                EvalCaseRun(
                    case_id=case.id,
                    case_class=case.case_class,
                    grader_type=case.grader_type,
                    attempts=0,
                    result="UNAVAILABLE",
                    reasons=(reason,),
                )
            )
            blockers.append(reason)
            continue

        attempt_count += 1
        grade = grade_candidate(case, candidate)
        reasons = tuple(_bounded(reason) for reason in grade.reasons)
        result = "PASS" if grade.passed else "FAIL"
        case_runs.append(
            EvalCaseRun(
                case_id=case.id,
                case_class=case.case_class,
                grader_type=grade.grader_type,
                attempts=1,
                result=result,
                reasons=reasons,
            )
        )
        if not grade.passed:
            blocker = _bounded(
                f"{case.id}: " + ("; ".join(reasons) if reasons else "deterministic grader failed")
            )
            blockers.append(blocker)

    if any(case.result == "FAIL" for case in case_runs):
        status = "FAIL"
    elif any(case.result == "UNAVAILABLE" for case in case_runs):
        status = "PARTIAL"
    else:
        status = "PASS"

    campaign = EvalCampaignResult(
        schema_version=SCHEMA_VERSION,
        mode="offline",
        cases=tuple(case_runs),
        attempt_count=attempt_count,
        blocking_failures=tuple(blockers),
        status=status,
    )
    _write_campaign(campaign)
    return campaign
