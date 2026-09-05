# CEK v1.0 Core Workflow Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove one representative Codex-native engineering loop from task classification through independent review and verification, with a machine-checkable sanitized evidence bundle and no maintainer-only hidden dependency.

**Architecture:** Keep existing orchestrator/agent/hook/state assets as the implementation baseline. Add a small workflow-evidence validator and run a real disposable-project acceptance; change core assets only when the acceptance exposes a reproducible defect.

**Tech Stack:** Markdown skills, TOML subagents, Python 3.11, native hooks, bounded state, `unittest`, local Codex runtime.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Do not add a new skill or agent merely to make the product look larger.
- `orchestrator` routes; it must not absorb domain documentation that belongs in progressive-disclosure skills.
- Independent review must run in a distinct agent/context boundary where the runtime supports it.
- Deterministic RED/GREEN/verification evidence outranks model confidence.
- The representative workflow must be runnable in a disposable fixture repository without the maintainer's private Codex skills.
- Local operator skills may help implement CEK but may not be required by the acceptance fixture.
- Evidence must omit raw private prompts, secrets, tokens, and machine-specific absolute paths.

---

### Task 1: Define a Machine-Checkable Representative Workflow Evidence Contract

**Files:**
- Create: `scripts/acceptance/workflow_evidence.py`
- Create: `tests/test_workflow_evidence.py`

**Interfaces:**
- Produces: `validate_workflow_record(record: dict[str, object]) -> tuple[str, ...]` and CLI `python scripts/acceptance/workflow_evidence.py validate --record <json>`.
- Required stages: `classify`, `plan`, `red`, `implement`, `green`, `review`, `verify`.

- [ ] **Step 1: Write failing tests for the evidence schema**

Tests must cover:

```python
REQUIRED_STAGES = ("classify", "plan", "red", "implement", "green", "review", "verify")
```

A valid record must contain:

```json
{
  "schemaVersion": 1,
  "repositoryCommit": "40-hex-sha",
  "runtimeVersion": "non-empty exact string",
  "fixture": "representative-workflow-v1",
  "stages": [
    {"name": "classify", "result": "PASS", "evidence": ["repo-relative-or-sanitized-note"]}
  ],
  "result": "PASS"
}
```

Tests must reject missing stages, duplicate stages, non-40-hex SHA, `PASS` stage without evidence, absolute Windows/macOS/Linux home paths, `sessionId`, and token-like `ghp_`/`sk-` strings.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_workflow_evidence -v
```

Expected: FAIL because module/validator does not exist.

- [ ] **Step 3: Implement the minimal validator/CLI**

Implement only schema validation and sanitized output; do not make this script launch Codex.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_workflow_evidence -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/acceptance/workflow_evidence.py tests/test_workflow_evidence.py
git commit -m "test: add representative workflow evidence contract"
```

---

### Task 2: Create a Disposable Representative Fixture

**Files:**
- Create: `tests/fixtures/representative-workflow/README.md`
- Create: `tests/fixtures/representative-workflow/src/calculator.py`
- Create: `tests/fixtures/representative-workflow/tests/test_calculator.py`
- Create: `tests/fixtures/representative-workflow/task.md`
- Test: `tests/test_representative_fixture.py`

**Interfaces:**
- Produces: a tiny deterministic Python bug-fix task whose expected RED and GREEN states can be verified without network access.

- [ ] **Step 1: Define the fixture task**

`task.md` must request a bounded bug fix such as correcting `divide(a, b)` so division by zero raises `ValueError("division by zero")` while preserving normal division.

- [ ] **Step 2: Encode initial RED state**

Initial `calculator.py` deliberately returns `float("inf")` for zero divisor while the test expects `ValueError`.

- [ ] **Step 3: Add fixture contract test**

`tests/test_representative_fixture.py` must copy the fixture to a temporary directory, run its test command, and assert the pristine fixture fails for the expected assertion/reason. It must not mutate the checked-in fixture.

- [ ] **Step 4: Run fixture contract**

```bash
python -m unittest tests.test_representative_fixture -v
```

Expected: PASS because the outer contract successfully observes the fixture's intentional inner RED state.

- [ ] **Step 5: Commit**

```bash
git add tests/fixtures/representative-workflow tests/test_representative_fixture.py
git commit -m "test: add representative engineering workflow fixture"
```

---

### Task 3: Run the Real Codex-Native Workflow in a Disposable Copy

**Files:**
- Use: `skills/orchestrator/SKILL.md`
- Use: relevant shipped core/domain skill selected by routing
- Use: `.codex/agents/reviewer.toml`
- Use: `hooks/hooks.json`, `hooks/scripts/hook_dispatch.py`, `runtime/state.py`
- Produce local raw record, then commit sanitized summary: `docs/research/evidence/codex-v1-representative-workflow.md`

**Interfaces:**
- Consumes: exact supported runtime, exact CEK SHA, fixture from Task 2.
- Produces: real observed evidence for all seven stages plus hook/state/reviewer observations.

- [ ] **Step 1: Copy fixture into a disposable Git repository**

```powershell
$Work = Join-Path ([IO.Path]::GetTempPath()) ('cek-workflow-' + [guid]::NewGuid())
Copy-Item -Recurse tests/fixtures/representative-workflow $Work
git -C $Work init
git -C $Work add .
git -C $Work commit -m 'fixture: initial red state'
```

Expected: clean disposable repository with intentionally failing inner test.

- [ ] **Step 2: Ask Codex to execute the repository task using CEK**

The runtime prompt references only the checked-in fixture task and CEK's shipped assets. Required observed stages:

```text
classify -> plan -> run failing test -> minimal implementation -> passing test -> independent reviewer -> verification
```

No step may require a maintainer-local skill that is absent from CEK.

- [ ] **Step 3: Capture deterministic stage evidence**

Record command/test exit codes, changed-file list, reviewer completion, verification result, runtime version, CEK SHA, and sanitized hook/state observations into the local JSON record defined by Task 1.

- [ ] **Step 4: Validate the record**

```bash
python scripts/acceptance/workflow_evidence.py validate --record <local-workflow-record.json>
```

Expected: PASS only if every required stage has evidence.

- [ ] **Step 5: Verify final fixture behavior independently**

Run the fixture's Python tests outside the model session. Expected: GREEN and only task-relevant changes.

---

### Task 4: Fix Only Reproducible Core Defects Exposed by Acceptance

**Files:**
- Modify only as failures justify: `skills/orchestrator/SKILL.md`, `.codex/agents/*.toml`, `hooks/scripts/hook_dispatch.py`, `runtime/state.py`
- Add focused regression test beside the defect's existing test suite.

**Interfaces:**
- Consumes: a concrete failed acceptance observation.
- Produces: minimal defect fix plus regression test; no speculative refactor.

- [ ] **Step 1: For each failure, reproduce it with the smallest deterministic test possible**

```text
Agent/routing defect -> tests/test_agent_contract.py or a new focused routing contract
Hook defect -> tests/test_hook_dispatch.py
State defect -> state-focused unit test
Verification defect -> tests/test_verification_engine.py
```

- [ ] **Step 2: Run RED, implement minimal fix, run GREEN**

Use the exact focused test before and after the change.

- [ ] **Step 3: Re-run representative workflow after every accepted core fix**

The final acceptance record must correspond to the final core bytes, not a pre-fix commit.

---

### Task 5: Close Core Workflow Evidence

**Files:**
- Create/Update: `docs/research/evidence/codex-v1-representative-workflow.md`
- Test: all related suites.

- [ ] **Step 1: Run deterministic regressions**

```bash
python -m unittest tests.test_workflow_evidence -v
python -m unittest tests.test_representative_fixture -v
python -m unittest tests.test_agent_contract -v
python -m unittest tests.test_hook_contract -v
python -m unittest tests.test_hook_dispatch -v
python -m unittest tests.test_verification_engine -v
```

Expected: PASS.

- [ ] **Step 2: Independent reviewer gate**

Reviewer checks that the real workflow used only CEK-shipped capabilities, independent review actually occurred, deterministic RED/GREEN evidence exists, and sanitized evidence does not overclaim general runtime compatibility.

- [ ] **Step 3: Record exact final SHA**

```bash
git status --short
git rev-parse HEAD
```

Expected: clean tree and exact SHA named in the sanitized evidence.

---

## Completion Criteria

Core workflow hardening closes when the checked-in evidence contract passes, the fixture's initial RED state is deterministic, a real Codex run completes all seven required stages on the exact final CEK SHA, any exposed defects have focused regression tests, and an independent reviewer confirms there is no hidden maintainer-only dependency.