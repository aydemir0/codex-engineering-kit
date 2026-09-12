from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmarks.model import (
    BenchmarkCase,
    BenchmarkConfiguration,
    load_cases,
    load_configurations,
    planned_attempt_count,
)
from runtime.state import write_state
from benchmarks.report import BenchmarkReport, build_report, load_run_records


KIND = "authenticated-context-benchmark"
SMOKE_KIND = "authenticated-context-benchmark-smoke"
RETRY_POLICY = (
    "One attempt per planned tuple; no selective retries. A proven whole-campaign "
    "infrastructure defect invalidates the campaign and requires a new campaign ID."
)
EXECUTION_ISOLATION = {
    "approvalPolicy": "automatic-review",
    "apps": "disabled",
    "ephemeral": False,
    "skipHostSkillDiscoveryFeature": "enabled",
    "nativeSkillInstructions": "disabled",
    "parentCodexEnvironment": "scrubbed",
    "cekHooks": "plugin-native",
    "hookTrust": "persisted",
    "pluginSkills": "excluded",
    "rules": "ignored",
    "sandbox": "read-only",
    "sessionStorage": "disposable CODEX_HOME",
    "userConfig": "disposable-only",
}
TOOL_ITEM_TYPES = {
    "command_execution",
    "mcp_tool_call",
    "collaboration_tool_call",
    "collab_tool_call",
}
HEX_40 = re.compile(r"^[0-9a-f]{40}$")
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
RESPONSE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["findings", "verification"],
    "properties": {
        "findings": {
            "type": "array",
            "minItems": 1,
            "maxItems": 8,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["claim", "evidence"],
                "properties": {
                    "claim": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "minItems": 1,
                        "maxItems": 8,
                        "items": {"type": "string"},
                    },
                },
            },
        },
        "verification": {
            "type": "array",
            "maxItems": 8,
            "items": {"type": "string"},
        },
    },
}


def planned_attempts(
    cases: tuple[BenchmarkCase, ...],
    configurations: tuple[BenchmarkConfiguration, ...],
    repetitions: int,
) -> tuple[tuple[BenchmarkCase, BenchmarkConfiguration, int], ...]:
    planned_attempt_count(cases, configurations, repetitions)
    return tuple(
        (case, configuration, repeat)
        for case in sorted(cases, key=lambda item: item.id)
        for configuration in sorted(configurations, key=lambda item: item.id)
        for repeat in range(1, repetitions + 1)
    )


def _skill_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def build_attempt_prompt(
    case: BenchmarkCase,
    configuration: BenchmarkConfiguration,
    skill_root: Path,
) -> str:
    sections = [
        f"Benchmark case: {case.id}",
        f"Benchmark configuration: {configuration.id}",
        configuration.instruction,
        "Inspect only the files in the current fixture. Do not use network access or modify files.",
        case.prompt,
        (
            "Return only the JSON object required by the supplied output schema. Ground every "
            "finding in fixture file, symbol, or statement evidence."
        ),
    ]
    if configuration.id == "A":
        skill_files = sorted(skill_root.glob("*/SKILL.md"))
        sections.append(
            "Always-loaded CEK skill contracts:\n\n"
            + "\n\n".join(_skill_text(path) for path in skill_files)
        )
    elif configuration.id == "B" and case.required_skill:
        sections.append(
            "Progressively disclosed CEK skill contract:\n\n"
            + _skill_text(skill_root / case.required_skill / "SKILL.md")
        )
    elif configuration.id == "C":
        sections.append(
            "You must spawn the project-local explorer subagent for repository inspection, wait "
            "for it, and base the final JSON on its returned evidence. Do not perform the fixture "
            "inspection in the parent context."
        )
    return "\n\n".join(sections)


def _sha256(stdout: str, stderr: str) -> str:
    digest = hashlib.sha256()
    digest.update(stdout.encode("utf-8", errors="replace"))
    digest.update(b"\x00")
    digest.update(stderr.encode("utf-8", errors="replace"))
    return digest.hexdigest()


def _methodology_sha256(
    case_dir: Path,
    configuration_dir: Path,
    skill_root: Path,
    explorer_agent: Path,
    hook_manifest: Path,
    hook_dispatcher: Path,
) -> str:
    sources = [
        *((f"cases/{path.name}", path) for path in sorted(case_dir.glob("*.json"))),
        *((f"configurations/{path.name}", path) for path in sorted(configuration_dir.glob("*.json"))),
        *((f"skills/{path.parent.name}/SKILL.md", path) for path in sorted(skill_root.glob("*/SKILL.md"))),
        ("agents/explorer.toml", explorer_agent),
        ("hooks/hooks.json", hook_manifest),
        ("hooks/scripts/hook_dispatch.py", hook_dispatcher),
        ("scripts/acceptance/context_benchmark.py", Path(__file__)),
    ]
    digest = hashlib.sha256()
    for label, path in sources:
        digest.update(label.encode("utf-8"))
        digest.update(b"\x00")
        text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
        digest.update(text.encode("utf-8"))
        digest.update(b"\x00")
    return digest.hexdigest()


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    timeout_seconds: float,
    environment: dict[str, str],
    input_text: str | None = None,
) -> tuple[int | None, str, str, int, str | None]:
    started = time.monotonic_ns()
    try:
        process = subprocess.Popen(
            list(command),
            cwd=str(cwd),
            env=environment,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,
            start_new_session=os.name != "nt",
            shell=False,
        )
        stdout, stderr = process.communicate(input=input_text, timeout=timeout_seconds)
        return (
            process.returncode,
            stdout or "",
            stderr or "",
            max(0, (time.monotonic_ns() - started) // 1_000_000),
            None,
        )
    except subprocess.TimeoutExpired as exc:
        if os.name == "nt":
            try:
                process.send_signal(signal.CTRL_BREAK_EVENT)
            except OSError:
                process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        for stream in (process.stdout, process.stderr):
            if stream is not None:
                stream.close()

        def timeout_text(value: str | bytes | None) -> str:
            if value is None:
                return ""
            return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value

        return (
            None,
            timeout_text(exc.stdout),
            timeout_text(exc.stderr),
            max(0, (time.monotonic_ns() - started) // 1_000_000),
            "timeout",
        )
    except OSError:
        return (
            None,
            "",
            "",
            max(0, (time.monotonic_ns() - started) // 1_000_000),
            "start-failure",
        )


def _probe(
    codex_command: tuple[str, ...],
    repo_path: Path,
    environment: dict[str, str],
) -> str:
    exit_code, stdout, _, _, error = _run(
        (*codex_command, "--approve-for-me", "--version"),
        cwd=repo_path,
        timeout_seconds=15,
        environment=environment,
    )
    if error or exit_code != 0 or not stdout.strip():
        raise RuntimeError("Codex version probe failed")
    version = stdout.strip()
    exit_code, stdout, _, _, error = _run(
        (*codex_command, "--approve-for-me", "exec", "--help"),
        cwd=repo_path,
        timeout_seconds=15,
        environment=environment,
    )
    required = ("--json", "--ephemeral", "--ignore-user-config", "--sandbox", "--output-schema")
    if error or exit_code != 0 or any(flag not in stdout for flag in required):
        raise RuntimeError("Codex exec capability probe failed")
    exit_code, stdout, _, _, error = _run(
        (
            *codex_command,
            "-c",
            "orchestrator.skills.enabled=false",
            "-c",
            "skills.include_instructions=false",
            "--disable",
            "apps",
            "--enable",
            "skip_host_skill_discovery",
            "debug",
            "prompt-input",
            "isolation-probe",
        ),
        cwd=repo_path,
        timeout_seconds=15,
        environment=environment,
    )
    model_prompt = stdout.casefold()
    if (
        error
        or exit_code != 0
        or "<skills_instructions" in model_prompt
        or re.search(r"\.agents(?:\\+|/+)skills", model_prompt)
    ):
        raise RuntimeError("Codex model-visible skill isolation probe failed")
    return version


def _git_output(repo_path: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(repo_path),
        text=True,
        capture_output=True,
        check=False,
        shell=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("Git benchmark preflight failed")
    return completed.stdout.strip()


def _verify_candidate(repo_path: Path, cek_commit: str) -> None:
    if _git_output(repo_path, "rev-parse", "HEAD") != cek_commit:
        raise ValueError("CEK benchmark candidate does not match HEAD")
    if _git_output(repo_path, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("CEK benchmark candidate has tracked changes")


def _verify_fixture_pins(repo_path: Path, fixture_root: Path, cases: tuple[BenchmarkCase, ...]) -> str:
    commits = {case.repository_commit for case in cases}
    if len(commits) != 1:
        raise ValueError("benchmark cases do not share one fixture commit")
    commit = next(iter(commits))
    relative_root = fixture_root.resolve().relative_to(repo_path.resolve())
    for case in cases:
        relative = (relative_root / case.fixture).as_posix()
        completed = subprocess.run(
            ["git", "diff", "--quiet", commit, "--", relative],
            cwd=str(repo_path),
            check=False,
            shell=False,
        )
        if completed.returncode != 0:
            raise ValueError(f"fixture differs from pinned commit: {case.id}")
    return commit


def _events(stdout: str) -> tuple[list[dict[str, Any]], bool]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            return events, False
        if not isinstance(item, dict):
            return events, False
        events.append(item)
    return events, bool(events)


def _parse_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    final_text: str | None = None
    usage: dict[str, Any] | None = None
    tool_calls = 0
    for event in events:
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
        event_type = event.get("type")
        if event_type not in {"item.started", "item.completed"} or not isinstance(
            event.get("item"), dict
        ):
            continue
        item = event["item"]
        item_type = item.get("type")
        if event_type != "item.completed":
            continue
        if item_type == "agent_message" and isinstance(item.get("text"), str):
            final_text = item["text"]
        if item_type in TOOL_ITEM_TYPES:
            tool_calls += 1
    return {
        "finalText": final_text,
        "usage": usage,
        "toolCalls": tool_calls,
    }


def _hook_lifecycle(capture: bytes) -> tuple[bool, str | None]:
    starts: list[tuple[str, str]] = []
    stops: list[tuple[str, str]] = []
    try:
        lines = capture.decode("utf-8").splitlines()
    except UnicodeDecodeError:
        return False, None
    for line in lines:
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return False, None
        if not isinstance(event, dict):
            return False, None
        name = event.get("event")
        agent_id = event.get("agentId")
        agent_type = event.get("agentType")
        session_id = event.get("sessionId")
        if (
            name not in {"SubagentStart", "SubagentStop"}
            or not isinstance(agent_id, str)
            or not agent_id
            or agent_type != "explorer"
            or not isinstance(session_id, str)
            or not session_id
        ):
            continue
        target = starts if name == "SubagentStart" else stops
        target.append((agent_id, session_id))
    matched = len(starts) == 1 and len(stops) == 1 and starts[0] == stops[0]
    return matched, "hook-subagent-start-stop" if matched else None


def _token(value: object) -> dict[str, object]:
    if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
        return {"value": value, "source": "measured"}
    return {"value": None, "source": "unavailable"}


def _quality(case: BenchmarkCase, final_text: str | None) -> tuple[bool, list[int]]:
    if not final_text:
        return False, list(range(1, len(case.evidence_checks) + 1))
    folded = final_text.casefold()
    missing = [
        index
        for index, alternatives in enumerate(case.evidence_checks, start=1)
        if not any(term.casefold() in folded for term in alternatives)
    ]
    return not missing, missing


def _write_raw(path: Path, stdout: str, stderr: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stdout, encoding="utf-8", newline="\n")
    path.with_suffix(".stderr.txt").write_text(stderr, encoding="utf-8", newline="\n")


def _run_attempt(
    *,
    ordinal: int,
    case: BenchmarkCase,
    configuration: BenchmarkConfiguration,
    repeat: int,
    codex_command: tuple[str, ...],
    codex_version: str,
    fixture_root: Path,
    skill_root: Path,
    explorer_agent: Path,
    raw_dir: Path,
    model: str,
    reasoning: str,
    timeout_seconds: float,
    environment: dict[str, str],
) -> dict[str, Any]:
    hook_capture = b""
    with tempfile.TemporaryDirectory(prefix="cek-context-benchmark-") as temporary:
        work = Path(temporary)
        shutil.copytree(fixture_root / case.fixture, work, dirs_exist_ok=True)
        if configuration.id == "C":
            agent_dir = work / ".codex" / "agents"
            agent_dir.mkdir(parents=True)
            shutil.copyfile(explorer_agent, agent_dir / "explorer.toml")
        schema_path = work / "response-schema.json"
        schema_path.write_text(json.dumps(RESPONSE_SCHEMA, sort_keys=True), encoding="utf-8")
        prompt = build_attempt_prompt(case, configuration, skill_root)
        feature = ("--enable", "multi_agent") if configuration.id == "C" else ("--disable", "multi_agent")
        command = (
            *codex_command,
            "--approve-for-me",
            "exec",
            "--json",
            "--ignore-rules",
            "-c",
            "orchestrator.skills.enabled=false",
            "-c",
            "skills.include_instructions=false",
            "--enable",
            "skip_host_skill_discovery",
            "--color",
            "never",
            "--sandbox",
            "read-only",
            "--model",
            model,
            "-c",
            f'model_reasoning_effort="{reasoning}"',
            "--disable",
            "plugins",
            "--disable",
            "apps",
            *feature,
            "--output-schema",
            str(schema_path),
            "--skip-git-repo-check",
            "-C",
            str(work),
            "-",
        )
        attempt_env = dict(environment)
        attempt_env["CEK_BENCHMARK_REPEAT"] = str(repeat)
        exit_code, stdout, stderr, duration_ms, process_error = _run(
            command,
            cwd=work,
            timeout_seconds=timeout_seconds,
            environment=attempt_env,
            input_text=prompt,
        )
        hook_path = work / ".codex-kit" / "hooks" / "events.jsonl"
        if hook_path.is_file():
            hook_capture = hook_path.read_bytes()

    raw_path = raw_dir / f"{ordinal:03d}-{case.id}-{configuration.id}-r{repeat}.jsonl"
    _write_raw(raw_path, stdout, stderr)
    if configuration.id == "C":
        raw_path.with_suffix(".hooks.jsonl").write_bytes(hook_capture)
    events, valid_jsonl = _events(stdout)
    parsed = _parse_events(events)
    subagent_lifecycle, subagent_evidence_type = _hook_lifecycle(hook_capture)
    quality_passed, missing_checks = _quality(case, parsed["finalText"])
    usage = parsed["usage"] if isinstance(parsed["usage"], dict) else {}

    failure_kind: str | None = None
    if process_error:
        failure_kind = process_error
    elif exit_code != 0:
        failure_kind = "nonzero-exit"
    elif not valid_jsonl:
        failure_kind = "invalid-jsonl"
    elif parsed["usage"] is None:
        failure_kind = "missing-completion"
    elif parsed["finalText"] is None:
        failure_kind = "missing-final-response"
    elif configuration.id == "C" and not subagent_lifecycle:
        failure_kind = "missing-subagent-lifecycle"
    elif not quality_passed:
        failure_kind = "quality-contract"

    final_hash = (
        hashlib.sha256(parsed["finalText"].encode("utf-8")).hexdigest()
        if parsed["finalText"] is not None
        else None
    )
    return {
        "attemptOrdinal": ordinal,
        "caseId": case.id,
        "configurationId": configuration.id,
        "repeat": repeat,
        "status": "PASS" if failure_kind is None else "FAIL",
        "failureKind": failure_kind,
        "model": model,
        "reasoning": reasoning,
        "codexVersion": codex_version,
        "inputTokens": _token(usage.get("input_tokens")),
        "outputTokens": _token(usage.get("output_tokens")),
        "cachedInputTokens": _token(usage.get("cached_input_tokens")),
        "durationMs": duration_ms,
        "toolCalls": parsed["toolCalls"],
        "parentContextTokens": {"value": None, "source": "unavailable"},
        "subagentTokens": {"value": None, "source": "unavailable"},
        "qualityPassed": quality_passed,
        "missingEvidenceChecks": missing_checks,
        "subagentLifecycle": subagent_lifecycle,
        "subagentEvidenceType": subagent_evidence_type,
        "subagentRoleEvidence": "explorer" if subagent_lifecycle else None,
        "lifecycleCaptureSha256": hashlib.sha256(hook_capture).hexdigest() if hook_capture else None,
        "eventCount": len(events),
        "captureSha256": _sha256(stdout, stderr),
        "finalResponseSha256": final_hash,
    }


def run_context_benchmark(
    *,
    codex_command: tuple[str, ...],
    repo_path: Path,
    case_dir: Path,
    configuration_dir: Path,
    fixture_root: Path,
    skill_root: Path,
    explorer_agent: Path,
    hook_manifest: Path,
    hook_dispatcher: Path,
    output_path: Path,
    raw_dir: Path,
    cek_commit: str,
    campaign_id: str,
    model: str,
    reasoning: str,
    timeout_seconds: float,
    smoke: bool = False,
    environment: dict[str, str] | None = None,
    isolated_user_profile: Path | None = None,
    verify_candidate: bool = False,
) -> dict[str, Any]:
    repo_path = repo_path.resolve()
    if output_path.exists():
        raise FileExistsError(f"refusing to overwrite benchmark output: {output_path}")
    if verify_candidate:
        _verify_candidate(repo_path, cek_commit)
    cases = load_cases(case_dir)
    configurations = load_configurations(configuration_dir)
    fixture_commit = _verify_fixture_pins(repo_path, fixture_root, cases)
    env = dict(os.environ if environment is None else environment)
    codex_home = env.get("CODEX_HOME")
    env = {name: value for name, value in env.items() if not name.upper().startswith("CODEX_")}
    if codex_home:
        env["CODEX_HOME"] = codex_home
    if isolated_user_profile is not None:
        profile = isolated_user_profile.resolve()
        profile.mkdir(parents=True, exist_ok=True)
        inherited_profile = env.get("USERPROFILE")
        if inherited_profile and Path(inherited_profile).resolve() == profile:
            raise ValueError("isolated user profile must differ from inherited USERPROFILE")
        env["USERPROFILE"] = str(profile)
        if profile.drive:
            env["HOMEDRIVE"] = profile.drive
            env["HOMEPATH"] = str(profile)[len(profile.drive) :]
    codex_version = _probe(codex_command, repo_path, env)
    attempts = planned_attempts(cases, configurations, 3)
    if smoke:
        case = next(item for item in cases if item.id == "node-small-bug")
        configuration = next(item for item in configurations if item.id == "C")
        attempts = ((case, configuration, 1),)

    record: dict[str, Any] = {
        "campaignId": campaign_id,
        "counted": not smoke,
        "cekCommit": cek_commit,
        "fixtureCommit": fixture_commit,
        "methodologySha256": _methodology_sha256(
            case_dir,
            configuration_dir,
            skill_root,
            explorer_agent,
            hook_manifest,
            hook_dispatcher,
        ),
        "codexVersion": codex_version,
        "model": model,
        "reasoning": reasoning,
        "timeoutSeconds": timeout_seconds,
        "repetitions": 3,
        "retryPolicy": RETRY_POLICY,
        "executionIsolation": {
            **EXECUTION_ISOLATION,
            "userProfileEnvironment": "disposable" if isolated_user_profile is not None else "inherited",
        },
        "runs": [],
    }
    kind = SMOKE_KIND if smoke else KIND
    for ordinal, (case, configuration, repeat) in enumerate(attempts, start=1):
        record["runs"].append(
            _run_attempt(
                ordinal=ordinal,
                case=case,
                configuration=configuration,
                repeat=repeat,
                codex_command=codex_command,
                codex_version=codex_version,
                fixture_root=fixture_root,
                skill_root=skill_root,
                explorer_agent=explorer_agent,
                raw_dir=raw_dir,
                model=model,
                reasoning=reasoning,
                timeout_seconds=timeout_seconds,
                environment=env,
            )
        )
        payload = dict(record)
        payload["campaignStatus"] = "RUNNING"
        write_state(output_path, kind, payload)

    record["campaignStatus"] = "SMOKE" if smoke else "COMPLETE"
    if verify_candidate:
        record["candidateStable"] = (
            _git_output(repo_path, "rev-parse", "HEAD") == cek_commit
            and not _git_output(repo_path, "status", "--porcelain", "--untracked-files=no")
        )
    else:
        record["candidateStable"] = None
    write_state(output_path, kind, record)
    record.update({"schemaVersion": 1, "kind": kind})
    return record


def validate_campaign_file(
    path: Path,
    case_dir: Path,
    configuration_dir: Path,
    *,
    expected_commit: str,
    expected_methodology: str,
    skill_root: Path,
    explorer_agent: Path,
    hook_manifest: Path,
    hook_dispatcher: Path,
) -> BenchmarkReport:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("authenticated benchmark must be a JSON object")
    if record.get("schemaVersion") != 1 or record.get("kind") != KIND:
        raise ValueError("invalid authenticated benchmark identity")
    if record.get("counted") is not True or record.get("campaignStatus") != "COMPLETE":
        raise ValueError("authenticated benchmark campaign is not complete")
    if record.get("candidateStable") is not True:
        raise ValueError("benchmark candidate was not stable")
    if not HEX_40.fullmatch(expected_commit) or record.get("cekCommit") != expected_commit:
        raise ValueError("authenticated benchmark commit mismatch")
    recomputed_methodology = _methodology_sha256(
        case_dir,
        configuration_dir,
        skill_root,
        explorer_agent,
        hook_manifest,
        hook_dispatcher,
    )
    if record.get("methodologySha256") != recomputed_methodology:
        raise ValueError("authenticated benchmark recomputed methodology mismatch")
    if not HEX_64.fullmatch(expected_methodology) or expected_methodology != recomputed_methodology:
        raise ValueError("authenticated benchmark methodology mismatch")
    if record.get("retryPolicy") != RETRY_POLICY or record.get("repetitions") != 3:
        raise ValueError("authenticated benchmark retry or repetition contract mismatch")
    if record.get("executionIsolation") != {
        **EXECUTION_ISOLATION,
        "userProfileEnvironment": "disposable",
    }:
        raise ValueError("authenticated benchmark runtime isolation mismatch")
    for field in ("campaignId", "fixtureCommit", "codexVersion", "model", "reasoning"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            raise ValueError(f"authenticated benchmark missing {field}")

    runs_payload = record.get("runs")
    if not isinstance(runs_payload, list):
        raise ValueError("authenticated benchmark missing runs")
    if [item.get("attemptOrdinal") for item in runs_payload if isinstance(item, dict)] != list(range(1, 46)):
        raise ValueError("authenticated benchmark attempt ordinals are incomplete")
    forbidden_keys = {"sessionId", "session_id", "stdout", "stderr", "prompt", "finalText"}
    for item in runs_payload:
        if not isinstance(item, dict) or forbidden_keys.intersection(item):
            raise ValueError("authenticated benchmark contains raw or malformed run data")
        if not HEX_64.fullmatch(item.get("captureSha256", "")):
            raise ValueError("authenticated benchmark capture hash is invalid")
        if item.get("finalResponseSha256") is not None and not HEX_64.fullmatch(
            item["finalResponseSha256"]
        ):
            raise ValueError("authenticated benchmark response hash is invalid")
        for field in ("inputTokens", "outputTokens", "cachedInputTokens"):
            evidence = item.get(field)
            if not isinstance(evidence, dict) or evidence.get("source") not in {"measured", "unavailable"}:
                raise ValueError("authenticated benchmark contains unsupported token evidence")
        if item.get("status") == "PASS" and item.get("configurationId") == "C" and (
            item.get("subagentLifecycle") is not True
            or item.get("subagentEvidenceType") != "hook-subagent-start-stop"
            or item.get("subagentRoleEvidence") != "explorer"
            or not HEX_64.fullmatch(item.get("lifecycleCaptureSha256", ""))
        ):
            raise ValueError("authenticated benchmark passing C run lacks structured subagent evidence")

    cases = load_cases(case_dir)
    configurations = load_configurations(configuration_dir)
    report = build_report(load_run_records(path), cases, configurations, 3)
    if not report.complete:
        raise ValueError("authenticated benchmark does not contain exactly 45 unique runs")
    return report


def validate_usage_reset_evidence(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict) or record.get("schemaVersion") != 1:
        raise ValueError("invalid WS6 usage-reset evidence")
    if record.get("kind") != "ws6-usage-reset-evidence" or record.get("authorizedCredits") != 2:
        raise ValueError("invalid WS6 usage-reset authorization boundary")
    events = record.get("events")
    if not isinstance(events, list) or len(events) > 2:
        raise ValueError("invalid WS6 usage-reset event count")
    if record.get("redeemedCredits") != len(events):
        raise ValueError("invalid WS6 usage-reset redeemed count")
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict):
            raise ValueError("invalid WS6 usage-reset event")
        if event.get("sequence") != index or event.get("afterAttemptOrdinal") != index * 15:
            raise ValueError("invalid WS6 usage-reset attempt boundary")
        if event.get("outcome") != "reset" or event.get("source") != "codex-app-consume-usage-reset":
            raise ValueError("invalid WS6 usage-reset outcome")
        for field in ("precedingCaptureSha256", "rawToolOutputSha256"):
            if not HEX_64.fullmatch(event.get(field, "")):
                raise ValueError("invalid WS6 usage-reset receipt hash")
        if not isinstance(event.get("observedAt"), str) or not event["observedAt"].endswith("Z"):
            raise ValueError("invalid WS6 usage-reset observation time")
    return record


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the authenticated CEK context benchmark.")
    parser.add_argument("--codex", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--configurations", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, required=True)
    parser.add_argument("--skills", type=Path, required=True)
    parser.add_argument("--explorer-agent", type=Path, required=True)
    parser.add_argument("--hook-manifest", type=Path, required=True)
    parser.add_argument("--hook-dispatcher", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--cek-commit", required=True)
    parser.add_argument("--campaign-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--reasoning", required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--isolated-user-profile", type=Path, required=True)
    parser.add_argument("--smoke", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    environment = os.environ.copy()
    if args.codex_home:
        environment["CODEX_HOME"] = str(args.codex_home.resolve())
    record = run_context_benchmark(
        codex_command=(str(args.codex.resolve()),),
        repo_path=args.repo,
        case_dir=args.cases,
        configuration_dir=args.configurations,
        fixture_root=args.fixtures,
        skill_root=args.skills,
        explorer_agent=args.explorer_agent,
        hook_manifest=args.hook_manifest,
        hook_dispatcher=args.hook_dispatcher,
        output_path=args.output,
        raw_dir=args.raw_dir,
        cek_commit=args.cek_commit,
        campaign_id=args.campaign_id,
        model=args.model,
        reasoning=args.reasoning,
        timeout_seconds=args.timeout,
        smoke=args.smoke,
        environment=environment,
        isolated_user_profile=args.isolated_user_profile,
        verify_candidate=True,
    )
    print(json.dumps({
        "campaignId": record["campaignId"],
        "kind": record["kind"],
        "runs": len(record["runs"]),
        "failures": sum(item["status"] == "FAIL" for item in record["runs"]),
        "methodologySha256": record["methodologySha256"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
