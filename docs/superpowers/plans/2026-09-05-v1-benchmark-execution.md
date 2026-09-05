# CEK v1.0 Authenticated 45-Run Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Execute the existing fixed 5-case × 3-configuration × 3-repeat context benchmark as a reproducible authenticated Codex campaign and publish only measurements supported by the complete validated dataset.

**Architecture:** Keep `benchmarks/` as the protocol/report source of truth and add one authenticated campaign runner that executes every planned attempt in deterministic order, records sanitized run metadata, and refuses to produce a complete campaign when attempts are missing/duplicated. Reporting remains in `benchmarks.cli`/`benchmarks.report`.

**Tech Stack:** Python 3.11, authenticated Codex CLI `exec`, benchmark JSON cases/configurations, existing benchmark model/report code, SHA-bound fixture repositories.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Fixed campaign size is 5 cases × 3 configurations × 3 repetitions = 45 attempts.
- Do not drop failed/unavailable runs from the dataset.
- Do not replace missing attempts with estimates.
- Benchmark fixture commits remain pinned; a changed fixture requires a new benchmark identity rather than silently reusing old results.
- Raw authenticated output stays local; committed data must be sanitized and bounded.
- No "lean", token-saving, context-efficiency, faster, or cheaper marketing claim is allowed until the complete report supports the exact wording.
- If Codex telemetry does not expose a metric reliably, report that metric as unavailable rather than inventing a proxy without documenting it.

---

### Task 1: Add an Authenticated Context-Benchmark Runner

**Files:**
- Create: `scripts/acceptance/context_benchmark.py`
- Create: `tests/test_context_benchmark_runner.py`
- Reuse: `benchmarks/model.py`, `benchmarks/report.py`, `benchmarks/cases/*.json`, `benchmarks/configurations/*.json`

**Interfaces:**
- CLI:

```text
python scripts/acceptance/context_benchmark.py \
  --codex <path> \
  --repo <cek-repo> \
  --cases benchmarks/cases \
  --configurations benchmarks/configurations \
  --fixtures benchmarks/fixtures \
  --output <local-runs.jsonl> \
  --repetitions 3 \
  --timeout 180
```

- Produces exactly one JSONL record per attempted `{case, configuration, repetition}` tuple.

- [ ] **Step 1: Write failing runner tests**

Tests must assert:

```text
- planned attempt order is deterministic;
- 5×3×3 produces exactly 45 unique keys;
- duplicate keys are rejected;
- fixture repositoryCommit mismatch blocks that case;
- unavailable Codex produces explicit UNAVAILABLE records rather than fewer rows;
- stdout/stderr secrets are redacted and raw text is bounded;
- output includes exact codexVersion and CEK repositoryCommit;
- runner never marks campaign complete itself; completeness belongs to report validation.
```

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_context_benchmark_runner -v
```

Expected: FAIL because the runner does not exist.

- [ ] **Step 3: Implement minimal runner**

Each output record must include at minimum:

```json
{
  "caseId": "backend-design",
  "configurationId": "A",
  "repetition": 1,
  "result": "PASS|FAIL|UNAVAILABLE",
  "repositoryCommit": "<fixture sha>",
  "cekCommit": "<40-hex sha>",
  "codexVersion": "<exact version>",
  "elapsedMs": 0,
  "inputMetric": null,
  "outputMetric": null,
  "captureSha256": "<sha256>",
  "invariants": [{"text": "...", "passed": true}],
  "notes": "sanitized bounded text"
}
```

If reliable token/context metrics are available in the runtime output, store them under explicit metric names and add tests for parsing. If they are not available, keep metric fields `null`; do not synthesize token counts from character length.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_context_benchmark_runner -v
python -m unittest tests.test_benchmark_contract -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/acceptance/context_benchmark.py tests/test_context_benchmark_runner.py
git commit -m "feat: add authenticated context benchmark runner"
```

---

### Task 2: Validate the Fixed Protocol Before Spending Authenticated Runs

**Files:**
- Read: `benchmarks/cases/*.json`
- Read: `benchmarks/configurations/*.json`
- Test: `tests/test_benchmark_contract.py`

- [ ] **Step 1: Run protocol validation**

```bash
python -m benchmarks.cli validate --cases benchmarks/cases --configurations benchmarks/configurations
```

Expected:

```text
PASS: fixed benchmark protocol valid (45 planned attempts)
```

- [ ] **Step 2: Verify fixture commits**

For every case, verify its `repositoryCommit` matches the checked-out fixture snapshot identity expected by the benchmark contract. If a fixture changed since the pinned commit, stop and create a new protocol version instead of updating the SHA casually.

- [ ] **Step 3: Run benchmark regression tests**

```bash
python -m unittest tests.test_benchmark_contract -v
python -m unittest tests.test_codex_pressure -v
```

Expected: PASS.

---

### Task 3: Freeze the CEK Benchmark Candidate

**Files:**
- No repository modification during campaign.

- [ ] **Step 1: Record exact candidate**

```bash
git status --short
git rev-parse HEAD
```

Expected: clean tree; save the 40-character SHA as the CEK benchmark candidate.

- [ ] **Step 2: Record exact Codex runtime**

```powershell
& $env:CEK_CODEX_BENCHMARK --version
```

Expected: exact version string recorded. The campaign report must name this runtime; do not publish a generic "Codex" result without version identity.

---

### Task 4: Execute All 45 Authenticated Attempts

**Files:**
- Local output only during execution: e.g. `.codex-kit/benchmarks/v1-runs.jsonl`

- [ ] **Step 1: Run the campaign once**

```powershell
python scripts/acceptance/context_benchmark.py `
  --codex $env:CEK_CODEX_BENCHMARK `
  --repo . `
  --cases benchmarks/cases `
  --configurations benchmarks/configurations `
  --fixtures benchmarks/fixtures `
  --output .codex-kit/benchmarks/v1-runs.jsonl `
  --repetitions 3 `
  --timeout 180
```

Expected: exactly 45 records, including FAIL/UNAVAILABLE records if any attempt does not succeed.

- [ ] **Step 2: Do not rerun selectively**

If infrastructure failure invalidates the campaign as a whole, archive/hash the invalid local output, fix the infrastructure defect with tests, then restart the full 45-run campaign under a new campaign identity. Do not replace individual bad rows with hand-picked reruns.

---

### Task 5: Generate and Validate the Report

**Files:**
- Use: `benchmarks/cli.py`, `benchmarks/report.py`
- Create: sanitized `docs/research/evidence/codex-v1-context-benchmark.md`
- Create: sanitized machine-readable dataset/report path selected by the existing benchmark model, excluding raw prompts/private output
- Modify: `docs/benchmark.md` only after validation

- [ ] **Step 1: Generate report**

```bash
python -m benchmarks.cli report --runs .codex-kit/benchmarks/v1-runs.jsonl --cases benchmarks/cases --configurations benchmarks/configurations --json
```

Expected: `complete=true` and `observed=45/45` before any comparative claim is considered.

- [ ] **Step 2: Validate deterministic invariants**

```bash
python -m unittest tests.test_benchmark_contract -v
python -m unittest tests.test_context_benchmark_runner -v
```

Expected: PASS.

- [ ] **Step 3: Publish only supported metrics**

The evidence document must separate:

```text
measured values
missing/unavailable metrics
failed/unavailable attempts
statistical/experimental limitations
allowed public wording
forbidden extrapolations
```

If token/context metrics are unavailable, CEK may still report task success/invariant outcomes and timing when measured, but must not call the result a measured context-efficiency win.

---

### Task 6: Update Claim Contracts Only if Measurement Supports Them

**Files:**
- Modify conditionally: `release_contracts/claims.json`
- Modify conditionally: `docs/release/claim-evidence-matrix.md`
- Modify: `docs/benchmark.md`

- [ ] **Step 1: Add/upgrade a benchmark claim only when the validated report directly supports its exact wording**

A complete campaign does not automatically prove configuration B or C is better than A.

- [ ] **Step 2: Run release validators**

```bash
python -m unittest tests.test_release_contract -v
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Expected: PASS.

- [ ] **Step 3: Independent statistical/evidence review**

Reviewer confirms no selective reruns, no missing attempts, no unsupported token proxy, and no causal/generalized claim beyond the five fixed benchmark cases.

---

## Completion Criteria

The benchmark workstream closes when the runner is regression-tested, protocol remains fixed at 45 attempts, the exact CEK SHA/runtime are frozen, all 45 rows are retained, the report validates complete or the campaign is explicitly invalid/blocked, and public performance/context wording does not exceed measured evidence.