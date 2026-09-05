# CEK v1.0 Security Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish an explicit CEK threat model and deterministic security contracts for reusable instructions, hooks, state, installers, evidence, dependencies, and learned-content promotion.

**Architecture:** Security remains defense-in-depth around Codex trust controls, not a sandbox claim. Add a repository-specific threat model plus focused static/unit contracts; reuse existing hook/package/learning tests and reject any public wording that converts guardrails into containment guarantees.

**Tech Stack:** Markdown threat model, Python 3.11 `unittest`, PowerShell installer/learning tests, existing hook/package manager code, GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Never describe hooks, read-only agents, or instruction files as an OS/process sandbox.
- Never commit credentials, raw private transcripts, tokens, raw session identifiers, or user-home paths in evidence.
- Learned candidates remain non-executable and require explicit human promotion.
- Destructive/external actions must remain bounded by Codex/user approval and repository policy; CEK must not silently weaken those boundaries.
- External MCP/app credentials remain outside repository templates.
- Dependency/provenance changes require source/license review and pinned CI actions where technically supported.
- Security tests may block release; they must not be weakened to preserve marketing wording.

---

### Task 1: Add the CEK Threat Model

**Files:**
- Create: `docs/security/threat-model.md`
- Modify: `SECURITY.md`
- Create: `tests/test_security_contract.py`

**Interfaces:**
- Produces: named assets, trust boundaries, threats, mitigations, residual risks, and deterministic documentation requirements.

- [ ] **Step 1: Write failing documentation contract tests**

`tests/test_security_contract.py` must assert that the threat model names all of these threat families:

```text
prompt/instruction injection
unsafe shell/tool guidance
destructive writes
secrets and credentials
local-state leakage
MCP/app permission boundaries
dependency provenance
install/update ownership
learned-content promotion
plugin metadata/external URL trust
```

It must also assert the threat model contains the explicit sentence concept that hooks are guardrails, not a sandbox, and links `SECURITY.md`.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_security_contract -v
```

Expected: FAIL because the threat model does not yet exist.

- [ ] **Step 3: Create `docs/security/threat-model.md`**

Use this required structure:

```markdown
# CEK Threat Model

## Scope and non-goals
## Protected assets
## Trust boundaries
## Threats and mitigations
### Prompt/instruction injection
### Unsafe shell/tool guidance
### Destructive writes
### Secrets and credentials
### Local-state leakage
### MCP/app permission boundaries
### Dependency provenance
### Install/update ownership
### Learned-content promotion
### Plugin metadata and external URL trust
## Residual risks
## Security verification
## Reporting
```

For every threat section state: attacker/control source, affected asset, current mitigation, deterministic check where available, and residual risk.

- [ ] **Step 4: Update `SECURITY.md` to link the threat model**

Add a short pointer; do not duplicate the entire model.

- [ ] **Step 5: Run GREEN and commit**

```bash
python -m unittest tests.test_security_contract -v
python tests/validate_content.py
git add docs/security/threat-model.md SECURITY.md tests/test_security_contract.py
git commit -m "docs: add CEK v1 threat model"
```

Expected: PASS.

---

### Task 2: Enforce Evidence and Public-Artifact Sanitization

**Files:**
- Modify: `tests/test_security_contract.py`
- Modify only if a failure exposes a bug: `scripts/acceptance/plugin_compatibility.py`, `scripts/acceptance/workflow_evidence.py`, evidence writers

**Interfaces:**
- Produces: deterministic scan over public evidence/submission/release documents for high-risk secret/path leakage.

- [ ] **Step 1: Add targeted repository scanners**

Scan these paths recursively when present:

```text
docs/research/evidence/
docs/release/
docs/submission/
release_contracts/
```

Reject:

```text
\bghp_[A-Za-z0-9]{20,}\b
\bsk-[A-Za-z0-9]{20,}\b
[A-Za-z]:\\Users\\
/Users/
/home/
sessionId
Authorization: Bearer
```

Do not scan fixtures whose explicit purpose is testing redaction unless the fixture uses clearly fake short markers that cannot be mistaken for real credentials.

- [ ] **Step 2: Run tests**

```bash
python -m unittest tests.test_security_contract -v
```

Expected: PASS on sanitized repository evidence.

---

### Task 3: Harden Hook/State Boundaries with Regression Tests

**Files:**
- Modify: `tests/test_hook_dispatch.py`
- Modify: state-focused tests or create `tests/test_state_contract.py`
- Modify only if RED exposes a defect: `hooks/scripts/hook_dispatch.py`, `runtime/state.py`

**Interfaces:**
- Produces: deterministic evidence that sensitive payload fields are not persisted unnecessarily and unknown state schemas fail safely.

- [ ] **Step 1: Add hook sanitization RED tests**

Tests must feed event payloads containing fake `sessionId`, bearer/token-like values, and irrelevant nested prompt content, then assert persisted evidence/state contains only the bounded fields required by CEK behavior.

- [ ] **Step 2: Add state-schema RED tests**

Test current schema load/save plus an unknown future schema value. Unknown/incompatible schema must return a bounded error/status rather than silently treating the record as valid current state.

- [ ] **Step 3: Implement minimal fixes only if RED reproduces an actual defect**

Do not redesign the state system if current code already satisfies the new tests.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_hook_dispatch -v
python -m unittest tests.test_state_contract -v
```

Expected: PASS.

---

### Task 4: Verify Installer Ownership and Learning Promotion Boundaries

**Files:**
- Test: `tests/test_package_manager.py`
- Test: `tests/Test-Install.ps1`
- Test: `tests/Test-Learning.ps1`
- Modify only if failures justify: package/install/learning implementation

**Interfaces:**
- Produces: evidence that CEK does not silently overwrite/remove unowned content and learned candidates do not auto-promote/execute.

- [ ] **Step 1: Run package ownership tests**

```bash
python -m unittest tests.test_package_manager -v
```

Expected: PASS.

- [ ] **Step 2: On Windows run lifecycle tests**

```powershell
./tests/Test-Install.ps1
./tests/Test-Learning.ps1
```

Expected: PASS; forced replacement backs up unsafe targets, uninstall respects ownership hashes, learning remains review-gated.

- [ ] **Step 3: Add focused regression only for a reproducible failure**

Every fix begins with a failing test and is limited to the exposed boundary.

---

### Task 5: Enforce Dependency and CI Provenance

**Files:**
- Modify: `tests/test_security_contract.py`
- Read: `.github/workflows/*.yml`, `THIRD_PARTY_NOTICES.md`, `LICENSE`

**Interfaces:**
- Produces: static assurance that CI third-party actions use immutable SHA references and attribution files remain present.

- [ ] **Step 1: Add CI action pinning contract**

For each workflow line matching `uses: owner/repo@...`, require the ref after `@` to be a 40-character hexadecimal commit SHA; local actions such as `./path` are exempt.

- [ ] **Step 2: Assert provenance documents exist and name MIT licensing boundaries**

Require `LICENSE` and `THIRD_PARTY_NOTICES.md`; do not require copied upstream source.

- [ ] **Step 3: Run security suite**

```bash
python -m unittest tests.test_security_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

### Task 6: Independent Security Review and Closure

**Files:**
- Review: threat model plus changes from Tasks 1-5
- Record: sanitized security review evidence under `docs/research/evidence/` if it adds concrete findings/results.

- [ ] **Step 1: Fresh-context security reviewer checks**

```text
Review trust boundaries, injection exposure, shell/tool guidance, destructive actions, state/evidence leakage, MCP permissions, install ownership, learning promotion, dependency provenance, and branding/URL trust.
```

- [ ] **Step 2: Classify findings**

Critical/high findings block this workstream until fixed and regression-tested. Medium/low residual risks must be documented, not hidden.

- [ ] **Step 3: Final verification**

```bash
python -m unittest tests.test_security_contract -v
python -m unittest tests.test_hook_dispatch -v
python -m unittest tests.test_package_manager -v
python tests/validate_content.py
git status --short
git rev-parse HEAD
```

Expected: PASS, clean tree, exact reviewed SHA.

---

## Completion Criteria

Security hardening closes when the threat model covers all required families, public evidence passes secret/path sanitization, hook/state boundaries have regression tests, installer/learning safety tests pass, CI provenance is pinned/attributed, no critical/high finding remains open, and residual risks are explicit.