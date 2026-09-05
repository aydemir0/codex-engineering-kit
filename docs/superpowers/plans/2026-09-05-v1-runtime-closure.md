# CEK v1.0 Runtime Closure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace inherited/blocked Plan F runtime uncertainty with fresh exact-runtime evidence or an explicit narrowed support boundary for every v1-required Codex surface.

**Architecture:** Reuse the existing disposable plugin-copy helper and release-contract model. Run exact CLI/Desktop campaigns in isolated `CODEX_HOME` environments, record sanitized per-surface evidence, and update compatibility states only when the exact runtime/candidate SHA proves the surface.

**Tech Stack:** Codex CLI/Desktop runtimes, Python 3.11, `scripts/acceptance/plugin_compatibility.py`, JSONL hook events, release contracts, PowerShell on Windows.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Never infer Desktop PASS from CLI PASS.
- Never infer a new PASS solely from byte identity with historical evidence when a v1 fresh-runtime gate requires execution.
- Use disposable `CODEX_HOME`; do not reuse the maintainer's normal profile for acceptance.
- Record exact 40-character repository SHA and exact runtime version for every fresh campaign.
- Default native hook discovery and explicit-manifest hook override are separate surfaces.
- RISK-001 closes only if explicit manifest hooks PASS on every runtime baseline CEK publicly claims for that surface.
- SessionEnd timeout/lifecycle classification is independent from observing one graceful SessionEnd.
- Desktop parent-wait remains separate from native subagent existence.
- Evidence committed to the repo is sanitized; raw machine-local artifacts remain uncommitted.

---

### Task 1: Freeze Candidate and Verify Acceptance Helpers

**Files:**
- Test: `tests/test_plugin_compatibility.py`
- Read/Use: `scripts/acceptance/plugin_compatibility.py`

**Interfaces:**
- Consumes: candidate repository checkout.
- Produces: exact SHA plus validated helper behavior before runtime execution.

- [ ] **Step 1: Record candidate identity**

```powershell
git status --short
git rev-parse HEAD
```

Expected: clean tree; save the 40-character SHA as `$RepoSha`.

- [ ] **Step 2: Verify helper regression suite**

```powershell
python -m unittest tests.test_plugin_compatibility -v
```

Expected: PASS.

- [ ] **Step 3: Require exact runtime paths**

```powershell
if (-not $env:CEK_CODEX_0147) { throw 'CEK_CODEX_0147 is required' }
if (-not $env:CEK_CODEX_DESKTOP_0152) { throw 'CEK_CODEX_DESKTOP_0152 is required for Desktop acceptance' }
& $env:CEK_CODEX_0147 --version
& $env:CEK_CODEX_DESKTOP_0152 --version
```

Expected for the declared baselines: exact strings identify `0.147.0` and Desktop bundled `0.152.0`. If either executable is unavailable, record that runtime's required surfaces as BLOCKED; do not substitute another version.

---

### Task 2: Re-run Native Plugin and Discovery on CLI 0.147.0

**Files:**
- Use: `.codex-plugin/plugin.json`
- Use: `.agents/plugins/marketplace.json`
- Create sanitized evidence: `docs/research/evidence/codex-cli-0.147.0-v1-runtime-closure.md`

**Interfaces:**
- Consumes: exact CLI executable, candidate SHA.
- Produces: fresh v1 evidence for marketplace/install/list/available discovery and any directly observable skill/plugin surface.

- [ ] **Step 1: Create disposable Codex home**

```powershell
$TempRoot = Join-Path ([IO.Path]::GetTempPath()) ('cek-v1-cli-' + [guid]::NewGuid())
$CodexHome = Join-Path $TempRoot 'codex-home'
New-Item -ItemType Directory -Force $CodexHome | Out-Null
$env:CODEX_HOME = $CodexHome
```

- [ ] **Step 2: Run the proven plugin sequence**

```powershell
& $env:CEK_CODEX_0147 --version
& $env:CEK_CODEX_0147 plugin marketplace add (Get-Location).Path --json
& $env:CEK_CODEX_0147 plugin marketplace list --json
& $env:CEK_CODEX_0147 plugin list --available --json
& $env:CEK_CODEX_0147 plugin add 'codex-engineering-kit@codex-engineering-kit-dev' --json
& $env:CEK_CODEX_0147 plugin list --json
```

Expected: marketplace registration succeeds, CEK is `available` before install, then installed/enabled after `plugin add`.

- [ ] **Step 3: Record only sanitized observations**

Evidence must include OS, runtime version, candidate SHA, plugin version, commands, PASS/FAIL per surface, cleanup result, and hashes of any raw local artifact; remove absolute user paths, tokens, session IDs, and credentials.

- [ ] **Step 4: Clean disposable state**

```powershell
Remove-Item -Recurse -Force $TempRoot
Remove-Item Env:CODEX_HOME -ErrorAction SilentlyContinue
```

Expected: disposable home removed.

---

### Task 3: Test Default and Explicit Hook Modes Separately

**Files:**
- Use: `scripts/acceptance/plugin_compatibility.py`
- Use: `hooks/hooks.json`
- Use: `hooks/scripts/hook_dispatch.py`
- Test: `tests/test_hook_contract.py`, `tests/test_hook_dispatch.py`, `tests/test_plugin_compatibility.py`
- Create evidence for CLI and Desktop under `docs/research/evidence/`

**Interfaces:**
- Consumes: exact runtime executable and candidate SHA.
- Produces: independent results for default hook discovery, explicit manifest override, lifecycle events, PreToolUse allow/deny, and SessionEnd observation.

- [ ] **Step 1: Prepare default disposable copy**

```powershell
$DefaultCopy = Join-Path ([IO.Path]::GetTempPath()) ('cek-default-' + [guid]::NewGuid())
python scripts/acceptance/plugin_compatibility.py prepare --repo . --destination $DefaultCopy --manifest-mode default
```

Expected: PASS; copied manifest contains no explicit `hooks` field.

- [ ] **Step 2: Prepare explicit-hooks disposable copy**

```powershell
$ExplicitCopy = Join-Path ([IO.Path]::GetTempPath()) ('cek-explicit-' + [guid]::NewGuid())
python scripts/acceptance/plugin_compatibility.py prepare --repo . --destination $ExplicitCopy --manifest-mode explicit-hooks
```

Expected: PASS; only the disposable manifest receives `"hooks": "./hooks/hooks.json"`.

- [ ] **Step 3: Execute the same bounded lifecycle fixture against each exact runtime/mode**

Use the repository's existing hook acceptance procedure/fixture that emits JSONL events. For every `{CLI 0.147.0, Desktop 0.152.0} × {default, explicit-hooks}` pair, retain the raw JSONL locally and summarize it with:

```powershell
python scripts/acceptance/plugin_compatibility.py summarize `
  --events <events.jsonl> `
  --expected-runtime <exact-expected-version> `
  --actual-runtime <observed-version> `
  --manifest-mode <default-or-explicit-hooks> `
  --repo-sha $RepoSha `
  --output <local-summary.json>
```

Expected: PASS only when SessionStart, PreToolUse allow, acceptance deny, PostToolUse, SessionEnd, and one bounded session are all observed. If the runtime cannot complete the fixture, record FAIL/BLOCKED rather than editing the helper to accept incomplete evidence.

- [ ] **Step 4: Re-run deterministic hook tests**

```powershell
python -m unittest tests.test_hook_contract -v
python -m unittest tests.test_hook_dispatch -v
python -m unittest tests.test_plugin_compatibility -v
```

Expected: PASS.

---

### Task 4: Re-run Native Subagent, Compaction, SessionEnd and Desktop Parent-Wait Probes

**Files:**
- Use: `.codex/config.toml`
- Use: `.codex/agents/explorer.toml`
- Use: `runtime/state.py`
- Use: `hooks/scripts/hook_dispatch.py`
- Create sanitized v1 evidence records under `docs/research/evidence/`

**Interfaces:**
- Consumes: exact runtime/candidate plus current Plan C procedure as the behavioral fixture.
- Produces: fresh per-surface PASS/FAIL/BLOCKED classification.

- [ ] **Step 1: Re-run the current native subagent fixture without changing agent bytes**

```text
Required observations:
- parent starts a real project-local custom subagent;
- SubagentStart and SubagentStop are observed;
- expected agent identity is recorded without raw private prompts;
- parent resumes after child completion or the runtime-specific wait behavior is classified.
```

- [ ] **Step 2: Re-run bounded compaction continuation**

```text
Required observations:
- pre-compaction state is written through current runtime/state.py;
- PreCompact/PostCompact hooks occur where the runtime exposes them;
- continuation after compaction uses the expected bounded state schema;
- unknown/incompatible state is not silently treated as valid.
```

- [ ] **Step 3: Classify SessionEnd timeout behavior explicitly**

```text
PASS requires both lifecycle observation and the documented v1 timeout-budget expectation to behave predictably.
If graceful SessionEnd occurs but timeout semantics remain unresolved, keep the SessionEnd classification LIMITED/BLOCKED according to the release model.
```

- [ ] **Step 4: Classify Desktop parent-wait separately**

```text
Record whether Desktop visibly waits, detaches, times out, or produces another reproducible parent/child lifecycle. Do not convert this observation into a general native-subagent PASS unless the subagent lifecycle itself also passes.
```

---

### Task 5: Update Compatibility Contracts from Evidence Only

**Files:**
- Modify: `release_contracts/compatibility.json`
- Modify as supported: `release_contracts/claims.json`
- Modify: `docs/release/compatibility-matrix.md`
- Modify: `docs/release/claim-evidence-matrix.md`
- Later consumed by v1 release checklist

**Interfaces:**
- Consumes: sanitized fresh runtime evidence from Tasks 2-4.
- Produces: machine-readable and human-readable identical runtime boundaries.

- [ ] **Step 1: Update each surface independently**

For every compatibility record, set only `PASS`, `FAIL`, `BLOCKED`, or `NOT_RUN` supported by the fresh campaign. Evidence paths must be repository-relative.

- [ ] **Step 2: Keep RISK-001 open unless explicit hooks pass both claimed baselines**

```text
If explicit-hooks CLI != PASS or explicit-hooks Desktop != PASS:
RISK-001 remains open and the primary plugin manifest continues to omit an explicit hooks field.
```

- [ ] **Step 3: Run release validators**

```powershell
python -m unittest tests.test_release_contract -v
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Expected: PASS.

- [ ] **Step 4: Independent reviewer gate**

Reviewer must verify exact runtime version, exact SHA, evidence path, no cross-runtime inference, and no hidden raw sensitive data for every upgraded PASS.

---

## Completion Criteria

Runtime closure is complete when every v1-required surface has fresh exact-runtime evidence or an explicit narrowed/excluded support boundary; RISK-001, SessionEnd, and Desktop parent-wait each have independent dispositions; release contracts validate; and no current BLOCKED/NOT_RUN state was upgraded by inference.