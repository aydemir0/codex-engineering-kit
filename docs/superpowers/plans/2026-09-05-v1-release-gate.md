# CEK v1.0 Exact-SHA Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce exactly one evidence-backed v1.0 release decision while preserving a verifiable link between the runtime-tested content candidate and the final evidence-bearing release commit.

**Architecture:** Freeze a **content candidate SHA** containing all runtime-affecting bytes, execute deterministic/CI/runtime/benchmark gates on that SHA, then create at most an evidence-only closure commit whose changed paths are explicitly whitelisted. The final release commit must pass deterministic CI and prove that runtime-critical bytes are identical to the tested content candidate; no self-referential commit SHA is embedded inside the commit that defines itself.

**Tech Stack:** Python 3.11 `unittest`, PowerShell 7 tests, release-contract JSON, Git/GitHub Actions, exact Git diff/provenance checks, Markdown release notes.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Final decision is exactly `READY` or `BLOCKED`.
- Runtime evidence is collected on a frozen content candidate SHA.
- Final release commit may reuse that runtime evidence only when every post-candidate change is evidence/claim metadata and a reviewer proves runtime-critical bytes are unchanged.
- Allowed post-candidate evidence paths are limited to `docs/research/evidence/`, `docs/release/`, and `release_contracts/` unless this plan is explicitly revised and re-reviewed.
- No skill, agent, hook, runtime helper, installer, workflow behavior, benchmark runner/protocol, plugin manifest, marketplace metadata, test fixture, or executable script may change in the evidence-only closure commit.
- Required deterministic CI must run on the final release commit SHA.
- A green deterministic CI matrix does not replace runtime acceptance.
- Benchmark success does not imply runtime compatibility; runtime PASS does not imply benchmark superiority.
- No critical/high security finding may remain open for READY.
- OpenAI-facing assets must not imply endorsement.
- Do not merge, tag, publish a GitHub release, or submit to OpenAI automatically; present verified choices to the user after the gate.
- If v0.2 PR #2 has not been integrated when v1 is ready, resolve stacked-branch/base history explicitly before main-branch release action.

---

### Task 1: Create the v1 Release Checklist Contract

**Files:**
- Create: `docs/release/v1.0-readiness.md`
- Create: `tests/test_v1_release_gate.py`
- Read: `release_contracts/claims.json`, `release_contracts/compatibility.json`

**Interfaces:**
- Produces: one checklist with sections `Architecture`, `Runtime`, `Reliability`, `Security`, `Engineering`, `UX`, `Evidence`, `Presentation`, one provenance section, and one final decision line.

- [ ] **Step 1: Write failing tests**

`tests/test_v1_release_gate.py` must require:

```text
all eight gate section headings
`## Release provenance`
exactly one line beginning `Final v1.0 decision: `
value is READY or BLOCKED
READY is forbidden while any required compatibility surface is FAIL/BLOCKED/NOT_RUN
READY is forbidden while the checklist names an open critical/high security blocker
READY is forbidden without a documented content-candidate provenance method
READY is forbidden without final-commit deterministic CI evidence
READY is forbidden while the presentation gate is open
```

The test must not require READY; BLOCKED is a valid honest state.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_v1_release_gate -v
```

Expected: FAIL because the v1 checklist does not exist.

- [ ] **Step 3: Create the initial BLOCKED checklist**

Required skeleton:

```markdown
# CEK v1.0 Readiness

## Architecture
## Runtime
## Reliability
## Security
## Engineering
## UX
## Evidence
## Presentation
## Release provenance

The runtime-tested content candidate and final release commit are identified by Git/GitHub evidence, not by embedding a commit hash into the commit that defines itself.

Final v1.0 decision: BLOCKED
```

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_v1_release_gate -v
```

Expected: PASS with honest BLOCKED state.

---

### Task 2: Populate Pre-Release Gate Evidence

**Files:**
- Modify: `docs/release/v1.0-readiness.md`
- Modify conditionally: `release_contracts/claims.json`, `release_contracts/compatibility.json`
- Read closure evidence from workstreams 1-8.

- [ ] **Step 1: Architecture gate**

Require green architecture truth contracts and reviewed truth-surface closure.

- [ ] **Step 2: Runtime gate preparation**

Define exactly which CLI/Desktop surfaces are in the public v1 support claim before executing the final runtime campaign. Excluded surfaces must be explicit limitations.

- [ ] **Step 3: Reliability gate**

Require representative workflow, state/hook regressions, and clean-install proof.

- [ ] **Step 4: Security gate**

Require threat model, deterministic security contracts, installer/learning safety, and no open critical/high finding.

- [ ] **Step 5: UX/evidence/presentation gates**

Require quick-start contracts, claim/compatibility validation, benchmark wording matching current measured state, reproducible demo, submission copy, owned/public cover asset, and verified GitHub metadata.

Keep `Final v1.0 decision: BLOCKED` until runtime/CI/provenance closure is complete.

---

### Task 3: Freeze and Test the Runtime-Affecting Content Candidate

**Files:**
- No repository modifications during the candidate campaign.

**Interfaces:**
- Produces: `$ContentCandidateSha` plus exact deterministic/CI/runtime/benchmark evidence.

- [ ] **Step 1: Verify clean tree and record content candidate SHA externally**

```bash
git status --short
git rev-parse HEAD
```

Expected: no status output and a 40-character SHA. Save it in the operator evidence log/CI notes; do not edit a tracked file just to insert that SHA.

- [ ] **Step 2: Run complete local deterministic suite**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tests/validate_content.py
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

On Windows:

```powershell
./tests/Test-Install.ps1
./tests/Test-Verify.ps1
./tests/Test-Learning.ps1
./tests/Test-Mcp.ps1
```

Expected: PASS.

- [ ] **Step 3: Require GitHub Actions on `$ContentCandidateSha`**

Record workflow run ID/head SHA/job conclusions externally. Do not use an older green run.

- [ ] **Step 4: Run required exact-runtime acceptance on `$ContentCandidateSha`**

Use the runtime-closure and clean-install plans. Every supported runtime surface must have PASS evidence on the declared baseline or the support claim must be narrowed before proceeding.

- [ ] **Step 5: Run/validate benchmark state on the same content candidate when benchmark claims are part of v1 public copy**

A measured claim requires the complete 45-run campaign tied to the content candidate/configuration identity. If no measured claim is made, the release must retain explicit no-measured-result wording.

---

### Task 4: Create the Evidence-Only Closure Commit

**Files allowed to change:**
- `docs/research/evidence/**`
- `docs/release/**`
- `release_contracts/**`

**Files forbidden to change after content-candidate runtime execution include:**
- `.codex-plugin/**`
- `.agents/**`
- `.codex/**`
- `skills/**`
- `hooks/**`
- `runtime/**`
- `scripts/**`
- `workflows/**`
- `benchmarks/**`
- `tests/fixtures/**`
- installer/package implementation

- [ ] **Step 1: Write sanitized runtime/benchmark/CI evidence and final claim states**

Update only allowed evidence/claim paths. If a required fix touches a forbidden path, abandon the candidate, implement the fix normally, and restart Task 3 on a new content candidate.

- [ ] **Step 2: Set the decision to READY only if every gate is already satisfied**

Otherwise preserve:

```text
Final v1.0 decision: BLOCKED
```

- [ ] **Step 3: Commit the evidence-only closure**

```bash
git status --short
git add docs/research/evidence docs/release release_contracts
git commit -m "docs: close CEK v1.0 release evidence"
```

Save the resulting 40-character SHA externally as `$ReleaseCommitSha`.

---

### Task 5: Prove Content-Candidate -> Release-Commit Provenance

**Files:**
- Create test/helper if useful: `tests/test_release_provenance.py`
- No runtime-affecting edits.

- [ ] **Step 1: List every changed path between the runtime-tested candidate and release commit**

```bash
git diff --name-only $ContentCandidateSha $ReleaseCommitSha
```

Expected: every path begins with exactly one of:

```text
docs/research/evidence/
docs/release/
release_contracts/
```

Any other path invalidates runtime-evidence reuse and requires a new content candidate/runtime campaign.

- [ ] **Step 2: Verify runtime-critical trees are identical**

Compare tree/blob identities or zero diffs for:

```bash
git diff --exit-code $ContentCandidateSha $ReleaseCommitSha -- .codex-plugin .agents .codex skills hooks runtime scripts workflows benchmarks tests/fixtures
```

Expected: exit `0`, no diff.

- [ ] **Step 3: Independent reviewer confirms the whitelist/provenance rule**

The reviewer must explicitly state that final release runtime claims inherit from the tested content candidate only because runtime-affecting bytes are unchanged.

---

### Task 6: Run Final Deterministic CI on the Release Commit

**Files:**
- No changes during verification.

- [ ] **Step 1: Run final local deterministic suite on `$ReleaseCommitSha`**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
python tests/validate_content.py
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Expected: PASS.

- [ ] **Step 2: Require fresh GitHub Actions on `$ReleaseCommitSha`**

Record workflow run ID/head SHA/job conclusions. All required jobs must be `success` on the release commit.

- [ ] **Step 3: If final CI fails**

Do not tag/release. Any fix creates a new release commit; if it touches runtime-affecting paths, restart from Task 3 with a new content candidate.

---

### Task 7: Independent Final Public-Surface Review

- [ ] **Step 1: Reviewer reads only public v1 surfaces plus evidence matrices**

Review correctness, stale versions/counts, unsupported compatibility, security omissions, hidden local dependencies, benchmark wording, and implied OpenAI endorsement.

- [ ] **Step 2: Any required source edit creates a new release commit**

If the edit touches runtime-affecting paths, runtime provenance is invalid and Task 3 restarts. Evidence-only edits may preserve the candidate only if Task 5 is rerun and final CI is rerun.

---

### Task 8: Confirm Exactly One Final Decision

**Files:**
- `docs/release/v1.0-readiness.md`
- `docs/release/v1.0-release-notes.md`

- [ ] **Step 1: Verify decision semantics**

```text
READY  = every applicable gate closed; content-candidate runtime evidence is valid; evidence-only provenance passes; final release commit CI passes.
BLOCKED = any required gate unresolved.
```

- [ ] **Step 2: Verify exactly one decision line**

```bash
python -m unittest tests.test_v1_release_gate -v
python -m unittest tests.test_release_contract -v
python -m unittest tests.test_submission_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

### Task 9: Present Integration and Submission Choices to the User

- [ ] **Step 1: If BLOCKED, report exact blockers and stop**

No merge/tag/release/submission action is presented as complete.

- [ ] **Step 2: If READY, present explicit choices**

```text
1. Merge/PR integration path
2. Create v1.0 tag/GitHub release on the verified release commit
3. Submit OpenAI Showcase package
4. Perform only plugin/workspace distribution steps actually available to the account
5. Keep the verified branch unchanged
```

User chooses externally visible actions. Do not execute merge/tag/release/submission without explicit approval.

---

## Completion Criteria

The release gate closes when one runtime-tested content candidate has green deterministic/CI/runtime evidence, the final evidence-bearing release commit differs only by whitelisted non-runtime paths, that provenance is independently verified, final release-commit CI is green, security/UX/presentation/benchmark wording gates are closed, and exactly one `READY` or `BLOCKED` decision remains. Public release actions occur only after READY plus explicit user approval.