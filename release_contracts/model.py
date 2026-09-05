from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

CLAIM_STATES = {"IMPLEMENTED", "VERIFIED", "LIMITED", "PLANNED"}
COMPATIBILITY_STATES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}


@dataclass(frozen=True)
class ClaimRecord:
    id: str
    wording: str
    state: str
    implementation_evidence: tuple[str, ...]
    runtime_evidence: tuple[str, ...]
    runtime_scope: str
    limitation: str
    public_wording: str


@dataclass(frozen=True)
class CompatibilityResult:
    status: str
    evidence: tuple[str, ...]
    limitation: str


@dataclass(frozen=True)
class CompatibilityRecord:
    surface: str
    cli_0147: CompatibilityResult
    desktop_0152: CompatibilityResult


def _tuple_strings(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{label} must be an array of strings")
    return tuple(value)


def load_claims(path: Path) -> tuple[ClaimRecord, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("claims") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("claims.json must contain a claims array")
    records: list[ClaimRecord] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"claims[{index}] must be an object")
        records.append(
            ClaimRecord(
                id=str(row.get("id", "")),
                wording=str(row.get("wording", "")),
                state=str(row.get("state", "")),
                implementation_evidence=_tuple_strings(
                    row.get("implementationEvidence", []),
                    f"claims[{index}].implementationEvidence",
                ),
                runtime_evidence=_tuple_strings(
                    row.get("runtimeEvidence", []),
                    f"claims[{index}].runtimeEvidence",
                ),
                runtime_scope=str(row.get("runtimeScope", "")),
                limitation=str(row.get("limitation", "")),
                public_wording=str(row.get("publicWording", "")),
            )
        )
    return tuple(records)


def _load_compatibility_result(value: object, label: str) -> CompatibilityResult:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be an object")
    return CompatibilityResult(
        status=str(value.get("status", "")),
        evidence=_tuple_strings(value.get("evidence", []), f"{label}.evidence"),
        limitation=str(value.get("limitation", "")),
    )


def load_compatibility(path: Path) -> tuple[CompatibilityRecord, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("compatibility") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("compatibility.json must contain a compatibility array")
    records: list[CompatibilityRecord] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"compatibility[{index}] must be an object")
        if "cli0147" not in row or "desktop0152" not in row:
            raise ValueError(f"compatibility[{index}] requires cli0147 and desktop0152")
        records.append(
            CompatibilityRecord(
                surface=str(row.get("surface", "")),
                cli_0147=_load_compatibility_result(row["cli0147"], f"compatibility[{index}].cli0147"),
                desktop_0152=_load_compatibility_result(
                    row["desktop0152"], f"compatibility[{index}].desktop0152"
                ),
            )
        )
    return tuple(records)


def _evidence_ref_error(value: str) -> str | None:
    if not value or value.strip() != value:
        return "evidence reference must be a non-empty repository-relative string"
    normalized = value.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", normalized):
        return "evidence reference must be repository-relative"
    if normalized.startswith("/"):
        return "evidence reference must be repository-relative"
    lowered = normalized.lower()
    if lowered.startswith(("users/", "home/", "tmp/")) or "/users/" in lowered:
        return "evidence reference must be repository-relative"
    if "../" in normalized or normalized == "..":
        return "evidence reference must stay inside the repository"
    return None


def _validate_evidence_refs(refs: Iterable[str], label: str, errors: list[str]) -> None:
    for value in refs:
        problem = _evidence_ref_error(value)
        if problem:
            errors.append(f"{label}: {problem}: {value!r}")


def validate_release_data(
    claims: Iterable[ClaimRecord],
    compatibility: Iterable[CompatibilityRecord],
) -> tuple[str, ...]:
    errors: list[str] = []
    claim_rows = tuple(claims)
    compatibility_rows = tuple(compatibility)

    seen_claims: set[str] = set()
    for claim in claim_rows:
        if not claim.id:
            errors.append("claim id must be non-empty")
        elif claim.id in seen_claims:
            errors.append(f"duplicate claim id: {claim.id}")
        seen_claims.add(claim.id)

        if claim.state not in CLAIM_STATES:
            errors.append(f"claim {claim.id}: invalid state {claim.state!r}")
        if claim.state in {"IMPLEMENTED", "VERIFIED", "LIMITED"} and not claim.implementation_evidence:
            errors.append(f"claim {claim.id}: {claim.state} requires implementation evidence")
        if claim.state == "VERIFIED":
            if not claim.runtime_evidence:
                errors.append(f"claim {claim.id}: VERIFIED requires runtime evidence")
            if not claim.runtime_scope:
                errors.append(f"claim {claim.id}: VERIFIED requires runtime scope")
        if claim.state == "LIMITED" and not claim.limitation:
            errors.append(f"claim {claim.id}: LIMITED requires a limitation")
        _validate_evidence_refs(claim.implementation_evidence, f"claim {claim.id}", errors)
        _validate_evidence_refs(claim.runtime_evidence, f"claim {claim.id}", errors)

    seen_surfaces: set[str] = set()
    for record in compatibility_rows:
        if not record.surface:
            errors.append("compatibility surface id must be non-empty")
        elif record.surface in seen_surfaces:
            errors.append(f"duplicate compatibility surface: {record.surface}")
        seen_surfaces.add(record.surface)

        for runtime_label, result in (
            ("cli0147", record.cli_0147),
            ("desktop0152", record.desktop_0152),
        ):
            if result.status not in COMPATIBILITY_STATES:
                errors.append(
                    f"compatibility {record.surface} {runtime_label}: invalid status {result.status!r}"
                )
            if result.status == "PASS" and not result.evidence:
                errors.append(
                    f"compatibility {record.surface} {runtime_label}: PASS requires evidence"
                )
            if result.status in {"FAIL", "BLOCKED"} and not result.limitation:
                errors.append(
                    f"compatibility {record.surface} {runtime_label}: {result.status} requires a limitation"
                )
            _validate_evidence_refs(
                result.evidence,
                f"compatibility {record.surface} {runtime_label}",
                errors,
            )

    return tuple(errors)
