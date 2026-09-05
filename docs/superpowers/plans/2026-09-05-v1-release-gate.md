# CEK v1.0 Exact-SHA Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce exactly one evidence-backed v1.0 release decision on an immutable candidate SHA and permit merge/tag/public release only when all required architecture, runtime, reliability, security, engineering, UX, evidence, and presentation gates are closed.

**Architecture:** Aggregate closure evidence from the first eight workstreams into a new v1 checklist. The checklist is derived from machine-readable claims/compatibility plus exact-SHA CI/runtime evidence; it never upgrades a blocker because the product looks complete.

**Tech Stack:** Python 3.11 `unittest`, PowerShell 7 tests, release-contract JSON, GitHub Actions, Git tags/releases, Markdown release notes.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Final decision is exactly `READY` or `BLOCKED`.
- Exact candidate SHA must be clean and immutable during final verification.
- Required CI must run on that exact SHA.
- Runtime evidence must name that exact SHA or the release claim must be narrowed to evidence that still applies by an explicitly reviewed provenance rule.
- A green deterministic CI matrix does not replace real runtime acceptance.
- A successful benchmark campaign does not imply runtime compatibility; runtime PASS does not imply benchmark superiority.
- No critical/high security finding may remain open for READY.
- OpenAI submission assets must not imply endorsement.
- Do not merge, tag, publish a GitHub release, or submit to OpenAI automatically; present verified choices to the user after the gate.
- If v0.2 PR #2 has not been integrated when v1 is ready, resolve the stacked-branch/base history explicitly before any main-branch release action.

---

### Task 1: Create the v1 Release Checklist Contract

**Files:**
- Create: `docs/release/v1.0-readiness.md`
- Create: `tests/test_v1_release_gate.py`
- Read: `release_contracts/claims.json`, `release_contracts/compatibility.json`

**Interfaces:**
- Produces: one checklist with sections `Architecture`, `Runtime`, `Reliability`, `Security`, `Engineering`, `UX`, `Evidence`, `Presentation`, and one final decision line.

- [ ] **Step 1: Write failing tests**

`tests/test_v1_release_gate.py` must require:

```text
all eight gate section headings
exactly one line beginning `Final v1.0 decision: `
value is READY or BLOCKED
READY is forbidden while any required compatibility surface is FAIL/BLOCKED/NOT_RUN
READY is forbidden while the checklist names an open critical/high security blocker
READY is forbidden without an exact candidate SHA
READY is forbidden without exact-SHA CI evidence
READY is forbidden while submission/presentation gate is open
```

The test must not require READY; BLOCKED is a valid honest state.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_v1_release_gate -v
```

Expected: FAIL because the v1 checklist does not exist.

- [ ] **Step 3: Create initial checklist as BLOCKED**

Required skeleton:

```markdown
# CEK v1.0 Readiness

Candidate SHA: not frozen

## Architecture
## Runtime
## Reliability
## Security
## Engineering
## UX
## Evidence
## Presentation

Final v1.0 decision: BLOCKED
```

Replace `not frozen` only when Task 3 freezes the real candidate.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_v1_release_gate -v
```

Expected: PASS with honest BLOCKED state.

---

### Task 2: Populate Gate Evidence from Closed Workstreams

**Files:**
- Modify: `docs/release/v1.0-readiness.md`
- Read: closure evidence from workstreams 1-8
- Modify conditionally: `release_contracts/claims.json`, `release_contracts/compatibility.json`

**Interfaces:**
- Consumes: exact closure SHAs/evidence.
- Produces: checklist rows that point to repository-relative proof or explicit blocker.

- [ ] **Step 1: Architecture gate**

Require green `tests.test_architecture_contract` and a reviewed truth-surface closure SHA.

- [ ] **Step 2: Runtime gate**

Require every runtime surface included in the public v1 support claim to be PASS on its named baseline. Surfaces excluded/narrowed from the public claim must be explicitly listed as limitations.

- [ ] **Step 3: Reliability gate**

Require representative workflow acceptance, state/hook regression suites, and clean-install proof.

- [ ] **Step 4: Security gate**

Require threat model, security contracts, installer/learning safety, and no open critical/high finding.

- [ ] **Step 5: Engineering gate**

Require complete deterministic unit/integration/acceptance suite and required CI.

- [ ] **Step 6: UX gate**

Require clean-install first-run reviewer journey and quick-start contracts.

- [ ] **Step 7: Evidence gate**

Require claim/compatibility validators plus benchmark wording matching actual measured state.

- [ ] **Step 8: Presentation gate**

Require reviewer-first README, architecture/demo, submission copy, owned public cover asset, and verified GitHub metadata.

---

### Task 3: Freeze the Final Candidate SHA

**Files:**
- Modify checklist candidate field only after clean tree.

- [ ] **Step 1: Verify clean repository**

```bash
git status --short
```

Expected: no output.

- [ ] **Step 2: Record exact candidate**

```bash
git rev-parse HEAD
```

Expected: 40-character SHA. Insert exactly that SHA into `docs/release/v1.0-readiness.md`, commit only the checklist update, then treat the resulting new checklist commit as the actual candidate SHA and repeat the identity step once so the checklist and candidate are self-consistent through the plan's chosen provenance convention.

- [ ] **Step 3: Do not edit implementation after freeze**

Any implementation/doc/test change creates a new candidate and restarts final verification.

---

### Task 4: Run the Complete Deterministic Candidate Suite

**Files:**
- No changes during verification.

- [ ] **Step 1: Run all Python tests**

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

Expected: PASS.

- [ ] **Step 2: Run content/release validators**

```bash
python tests/validate_content.py
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Expected: PASS.

- [ ] **Step 3: On Windows run PowerShell suites**

```powershell
./tests/Test-Install.ps1
./tests/Test-Verify.ps1
./tests/Test-Learning.ps1
./tests/Test-Mcp.ps1
```

Expected: PASS.

---

### Task 5: Require GitHub Actions on the Exact Candidate

**Files:**
- No source changes.

- [ ] **Step 1: Push candidate branch and obtain workflow run for the exact SHA**

Do not use an older green run.

- [ ] **Step 2: Verify every required job conclusion**

Record workflow run ID, head SHA, total jobs, and every required job conclusion in the v1 checklist/evidence.

Expected: all required deterministic jobs `success` on the exact candidate SHA.

- [ ] **Step 3: If CI reveals a failure**

Unfreeze the candidate, reproduce locally where possible, fix through TDD/systematic debugging, create a new SHA, and restart Tasks 3-5.

---

### Task 6: Verify Exact-SHA Runtime and Benchmark Evidence

**Files:**
- Read runtime/benchmark evidence, update checklist only.

- [ ] **Step 1: Runtime review**

For every supported runtime claim, verify evidence names the candidate SHA or has an explicitly reviewed byte/provenance equivalence acceptable under the release policy. Prefer fresh exact-SHA acceptance for v1.

- [ ] **Step 2: Benchmark review**

Require 45/45 complete validated dataset before any measured comparative wording; otherwise preserve no-measured-result language.

- [ ] **Step 3: Security/presentation external checks**

Re-verify GitHub description, public cover URL, and current OpenAI submission/distribution facts immediately before READY.

---

### Task 7: Independent Final Review

- [ ] **Step 1: Fresh reviewer reads only public v1 surfaces plus evidence matrices**

Review for correctness, overclaiming, stale versions/counts, unsupported compatibility, security omissions, hidden dependencies, misleading benchmark language, and implied OpenAI endorsement.

- [ ] **Step 2: Any major finding resets the candidate**

Fix, test, create new SHA, and restart exact-SHA verification.

- [ ] **Step 3: Minor editorial findings may only be fixed by creating a new candidate**

There is no "docs-only exception" to exact-SHA release verification.

---

### Task 8: Set Exactly One Final Decision

**Files:**
- Modify: `docs/release/v1.0-readiness.md`
- Create: `docs/release/v1.0-release-notes.md` only if READY or as a clearly unreleased candidate note if BLOCKED.

- [ ] **Step 1: Determine decision mechanically from gates**

```text
READY  = every applicable gate closed with evidence on the final candidate.
BLOCKED = one or more required gates unresolved.
```

- [ ] **Step 2: Update final decision line once**

```text
Final v1.0 decision: READY
```

or

```text
Final v1.0 decision: BLOCKED
```

Never include both.

- [ ] **Step 3: Run final gate tests**

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
2. Create v1.0 tag/GitHub release
3. Submit OpenAI Showcase package
4. Perform available plugin/workspace distribution steps
5. Keep candidate branch unchanged
```

User chooses externally visible actions. Do not execute merge/tag/release/submission without explicit approval.

---

## Completion Criteria

The release-gate workstream closes when one exact candidate SHA has green required deterministic CI, supported runtime evidence, closed security/reliability/UX/presentation gates, benchmark wording aligned with measured state, independent final review, and exactly one `READY` or `BLOCKED` decision. Public release actions occur only after READY plus explicit user approval.