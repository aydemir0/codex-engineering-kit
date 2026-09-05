# Codex Engineering Kit v1.0 OpenAI-Ready Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn CEK from the proven v0.2 implementation boundary into a Codex-native, evidence-bound, clean-installable, security-reviewed, benchmarked, and OpenAI-submission-ready v1.0 product.

**Architecture:** Execute nine independent evidence-gated workstreams. Each workstream has its own detailed implementation plan and can be reviewed or rejected independently; the final v1.0 release gate consumes only closed workstream evidence and never upgrades blocked runtime surfaces by inference.

**Tech Stack:** OpenAI Codex native plugin metadata, Markdown skills, TOML subagents, Python 3.11+, PowerShell 7+, JSON release contracts, `unittest`, Git/GitHub Actions on Ubuntu/Windows/macOS.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Public product identity remains **Codex Engineering Kit**; CEK is an independent community project and must not imply OpenAI, Anthropic, or ECC endorsement.
- Prefer native Codex plugin, skill, subagent, hook, and task surfaces over compatibility shims.
- Public wording cannot exceed deterministic or exact-runtime evidence.
- Keep always-visible context small; use progressive disclosure and isolated subagents only when they close a real context or review gap.
- New skills/agents require a demonstrated workflow gap; there is no marketing target for catalog size.
- Maintainer-local Codex skills are operator tooling, not CEK dependencies unless they separately pass CEK admission contracts.
- Hooks are guardrails and evidence collectors, not a security sandbox.
- Learned content remains review-gated and must never become an automatic execution source.
- No measured lean/token/context-efficiency claim is allowed until the authenticated 45-run A/B/C campaign is completed and validated.
- Three-OS repository CI is not blanket Codex runtime compatibility proof.
- Desktop evidence may not be inferred from CLI evidence.
- Unsupported or unobserved runtime surfaces remain `BLOCKED`/`NOT_RUN` or are excluded from the public support claim.
- Exact candidate SHA must be recorded for runtime acceptance and final release verification.
- No credentials, raw private transcripts, auth tokens, raw session identifiers, or machine-local sensitive state may be committed as evidence.
- v0.2 PR #2 remains the integration base until it is merged; v1 work must not silently merge or rewrite `main`.

---

## File/Subsystem Map

| Workstream | Primary surfaces | Detailed plan |
| --- | --- | --- |
| 1. Truth surface reconciliation | `README.md`, `docs/architecture.md`, `ROADMAP.md`, release docs, architecture contracts | `docs/superpowers/plans/2026-09-05-v1-truth-surface-reconciliation.md` |
| 2. Runtime closure | `scripts/acceptance/`, `tests/test_plugin_compatibility.py`, hook/runtime evidence, compatibility contracts | `docs/superpowers/plans/2026-09-05-v1-runtime-closure.md` |
| 3. Core workflow hardening | `skills/orchestrator/`, `.codex/agents/`, `hooks/`, `runtime/`, workflow acceptance | `docs/superpowers/plans/2026-09-05-v1-core-workflow-hardening.md` |
| 4. Security hardening | `SECURITY.md`, hooks/install/state checks, threat model, security tests | `docs/superpowers/plans/2026-09-05-v1-security-hardening.md` |
| 5. Skill/agent stocktake | `skills/`, `.codex/agents/`, routing/admission contracts | `docs/superpowers/plans/2026-09-05-v1-skill-agent-stocktake.md` |
| 6. Benchmark execution | `benchmarks/`, `tests/test_benchmark_contract.py`, benchmark evidence/report | `docs/superpowers/plans/2026-09-05-v1-benchmark-execution.md` |
| 7. Clean-install UX | `.codex-plugin/`, `.agents/plugins/`, installers, smoke/acceptance tests, quick start | `docs/superpowers/plans/2026-09-05-v1-clean-install-ux.md` |
| 8. OpenAI-ready presentation | README hierarchy, diagrams, demo script/assets, cover image brief, Showcase submission copy | `docs/superpowers/plans/2026-09-05-v1-openai-presentation.md` |
| 9. v1.0 release gate | release contracts, v1 checklist, exact-SHA CI/runtime evidence, tag/release decision | `docs/superpowers/plans/2026-09-05-v1-release-gate.md` |

## Ownership Model

- **ChatGPT lane:** cross-repository consistency, plan/spec enforcement, GitHub coordination, claim/evidence review, docs/release contracts, submission package.
- **Local Codex lane:** repository-local implementation, local CLI/Desktop acceptance, clean-install tests, shell/PowerShell execution, runtime behaviors unavailable in the ChatGPT harness.
- **Independent reviewer lane:** fresh-context review of each completed task for spec compliance, implementation quality, security, and overclaiming.
- A Codex result is usable release evidence only when runtime version, exact repository SHA, command/procedure, sanitized result, and status are recorded.

---

### Task 1: Close Truth Surface Reconciliation

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-truth-surface-reconciliation.md`
- Modify: `docs/architecture.md`
- Modify as required by failing contracts: `README.md`, `ROADMAP.md`, `SECURITY.md`
- Test: `tests/test_architecture_contract.py`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: v0.2 head `a1842b3e63fe15f3bf607833f5d1f43c6b41cb3b`, current plugin manifest, shipped skill directories, native agent TOMLs.
- Produces: one current architecture narrative plus deterministic drift contracts consumed by every later public/release workstream.

- [ ] **Step 1: Execute the detailed workstream plan**

```text
Read and execute:
docs/superpowers/plans/2026-09-05-v1-truth-surface-reconciliation.md
```

- [ ] **Step 2: Run closure tests**

```bash
python -m unittest tests.test_architecture_contract -v
python -m unittest tests.test_release_contract -v
python tests/validate_content.py
```

Expected: all commands exit `0`.

- [ ] **Step 3: Record workstream closure commit**

```bash
git status --short
git log -1 --oneline
```

Expected: clean tree after a dedicated truth-surface commit; record exact SHA in the master execution ledger.

---

### Task 2: Close Runtime Compatibility Decisions

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-runtime-closure.md`
- Modify: `scripts/acceptance/plugin_compatibility.py`
- Modify/Test: `tests/test_plugin_compatibility.py`, hook/runtime acceptance tests as required
- Modify: `release_contracts/compatibility.json`
- Modify: `docs/release/compatibility-matrix.md`
- Create/Update sanitized exact-runtime evidence under `docs/research/evidence/`

**Interfaces:**
- Consumes: exact candidate SHA and installed Codex CLI/Desktop runtime versions.
- Produces: evidence-backed disposition for Desktop 0.152.0 surfaces, explicit hooks/RISK-001, SessionEnd, Desktop parent-wait, and any support claim narrowed by unavailable runtime behavior.

- [ ] **Step 1: Execute the detailed runtime plan in the local Codex lane**

```text
Do not replace unavailable runtime execution with inference.
Capture exact runtime version + repository SHA before each acceptance campaign.
```

- [ ] **Step 2: Validate compatibility data**

```bash
python -m unittest tests.test_plugin_compatibility -v
python -m unittest tests.test_release_contract -v
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Expected: all commands exit `0`; blocked/not-run statuses remain explicit when evidence is unavailable.

- [ ] **Step 3: Reviewer gate**

```text
Reviewer checks that no CLI PASS has been copied to Desktop and no BLOCKED surface became PASS without exact runtime evidence.
```

---

### Task 3: Harden the Representative Engineering Workflow

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-core-workflow-hardening.md`
- Modify as justified: `skills/orchestrator/`, `.codex/agents/*.toml`, `hooks/`, `runtime/`
- Create/Modify: focused acceptance tests and sanitized workflow evidence

**Interfaces:**
- Consumes: truth-surface contracts and runtime decisions from Tasks 1-2.
- Produces: one reproducible representative flow demonstrating classify -> plan -> implement/test -> independent review -> verify -> evidence/state behavior without maintainer-only hidden dependencies.

- [ ] **Step 1: Execute the detailed workflow-hardening plan with TDD**

```text
Every behavior change starts with a failing focused contract/acceptance test.
Do not add new agents or skills solely to make the demo look larger.
```

- [ ] **Step 2: Run focused regression suites**

```bash
python -m unittest tests.test_agent_contract -v
python -m unittest tests.test_hook_contract -v
python -m unittest tests.test_hook_dispatch -v
python -m unittest tests.test_verification_engine -v
```

Expected: all commands exit `0` plus the new representative workflow acceptance suite passes.

---

### Task 4: Close the Security Hardening Gate

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-security-hardening.md`
- Modify: `SECURITY.md`
- Create: `docs/security/threat-model.md`
- Modify/Create tests for secrets, state, hook payload sanitization, installer ownership, and learned-content promotion

**Interfaces:**
- Consumes: actual workflow/runtime/install surfaces after Tasks 2-3.
- Produces: threat model, deterministic security contracts, explicit residual risks, and security-review evidence.

- [ ] **Step 1: Execute threat-model-driven test additions**

```text
Minimum threat families:
prompt/instruction injection
unsafe shell/tool guidance
destructive writes
secrets/credentials
local-state leakage
MCP/app permission boundaries
dependency provenance
install/update ownership
learned-content promotion
plugin metadata/external URL trust
```

- [ ] **Step 2: Run security-related repository checks**

```bash
python tests/validate_content.py
python -m unittest tests.test_hook_dispatch -v
python -m unittest tests.test_package_manager -v
```

Expected: exit `0`, plus all new security contract tests pass.

---

### Task 5: Complete Skill and Agent Stocktake

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-skill-agent-stocktake.md`
- Inspect/Modify: `skills/*/SKILL.md`, `.codex/agents/*.toml`
- Create: machine-readable admission/ownership index if justified by the detailed plan
- Test: skill/agent overlap, discovery, and routing contracts

**Interfaces:**
- Consumes: representative workflow evidence from Task 3.
- Produces: justified core/domain skill set and focused agent set with activation/output/mutation/completion contracts.

- [ ] **Step 1: Execute the stocktake plan**

```text
For each shipped skill/agent answer:
What unique workflow gap does it close?
When does it activate?
What evidence/output does it owe the parent?
What may it mutate?
What overlaps with another asset?
```

- [ ] **Step 2: Reject unjustified catalog growth**

```text
A local maintainer skill is not copied into CEK merely because it is useful during development.
```

- [ ] **Step 3: Run skill/agent contracts**

```bash
python -m unittest tests.test_agent_contract -v
python -m unittest tests.test_domain_skills -v
python tests/validate_content.py
```

Expected: exit `0` plus any new routing/admission contracts pass.

---

### Task 6: Execute and Publish the Authenticated 45-Run Benchmark

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-benchmark-execution.md`
- Use: `benchmarks/cases/*.json`, `benchmarks/configurations/*.json`, benchmark CLI/reporting
- Test: `tests/test_benchmark_contract.py`, `tests/test_codex_pressure.py`
- Create: sanitized measured run dataset/report under the detailed plan's evidence path
- Modify only after valid results: `docs/benchmark.md`, claim/evidence contracts

**Interfaces:**
- Consumes: stable workflow/skill/agent configuration from Tasks 3 and 5.
- Produces: validated A/B/C measurements or an explicit failed/invalid campaign; public performance wording remains absent unless the report supports it.

- [ ] **Step 1: Freeze candidate and benchmark fixture commit**

```bash
git rev-parse HEAD
git status --short
```

Expected: exact SHA recorded and clean tree before authenticated runs.

- [ ] **Step 2: Execute the detailed 45-run protocol using local authenticated Codex**

```text
5 cases × 3 configurations × 3 repeats = 45 runs.
Do not cherry-pick successful runs or replace missing runs with estimates.
```

- [ ] **Step 3: Validate report**

```bash
python -m unittest tests.test_benchmark_contract -v
python -m unittest tests.test_codex_pressure -v
```

Expected: exit `0`; measured claims are added only if the validated dataset supports them.

---

### Task 7: Close Clean-Install and First-Run UX

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-clean-install-ux.md`
- Modify: `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` only when evidence requires it
- Modify: installation/smoke helpers and tests
- Modify: README quick start after clean-install proof

**Interfaces:**
- Consumes: settled runtime support surface from Task 2 and stable shipped assets from Task 5.
- Produces: clean-environment install -> discover -> run -> verify journey with explicit failure guidance.

- [ ] **Step 1: Execute clean-install acceptance from a disposable environment**

```text
The acceptance record must state OS, Codex version, repository SHA, install path, discovery result, representative first workflow, and cleanup result.
```

- [ ] **Step 2: Run deterministic installer/plugin regressions**

```bash
python -m unittest tests.test_plugin_contract -v
python -m unittest tests.test_plugin_compatibility -v
python -m unittest tests.test_package_manager -v
```

On Windows also run:

```powershell
./tests/Test-Install.ps1
```

Expected: supported path passes; unsupported runtime paths remain explicitly documented.

---

### Task 8: Build the OpenAI-Ready Presentation Package

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-openai-presentation.md`
- Modify: `README.md`
- Create: current architecture diagram asset/source
- Create: demo script/storyboard and reproducible demo commands
- Create: `docs/submission/openai-showcase.md`
- Create: cover-image brief/source asset
- Modify: repository metadata externally where GitHub permissions allow; otherwise preserve a manual blocker

**Interfaces:**
- Consumes: only evidence closed by Tasks 1-7.
- Produces: 30-second, 5-minute, and deep technical reviewer paths plus complete OpenAI Showcase submission copy without unsupported claims.

- [ ] **Step 1: Execute the detailed presentation plan**

```text
Every public capability sentence must map to release evidence or be written as an explicit limitation/future item.
```

- [ ] **Step 2: Re-run public-surface contract checks**

```bash
python -m unittest tests.test_architecture_contract -v
python -m unittest tests.test_release_contract -v
python tests/validate_content.py
```

Expected: exit `0` and no stale counts/version/compatibility wording.

---

### Task 9: Make the v1.0 Release Decision

**Files:**
- Plan: `docs/superpowers/plans/2026-09-05-v1-release-gate.md`
- Create/Modify: v1 release checklist, claims, compatibility data, release notes, exact-SHA evidence
- No tag/release until READY gate is proven

**Interfaces:**
- Consumes: closure evidence from Tasks 1-8.
- Produces: exactly one evidence-backed decision: `READY` or `BLOCKED`; a tag/public release is permitted only for `READY`.

- [ ] **Step 1: Freeze release candidate SHA**

```bash
git status --short
git rev-parse HEAD
```

Expected: clean tree and exact candidate SHA recorded.

- [ ] **Step 2: Run complete deterministic candidate suite**

```bash
python tests/validate_content.py
python -m unittest tests.test_architecture_contract -v
python -m unittest tests.test_release_contract -v
python -m unittest tests.test_plugin_compatibility -v
python -m release_contracts.cli validate --claims release_contracts/claims.json --compatibility release_contracts/compatibility.json
```

Expected: exit `0`; full workflow-specific suites and required CI are also green on the exact SHA.

- [ ] **Step 3: Verify exact-SHA runtime evidence**

```text
Required declared runtime surfaces must be PASS on the exact supported baseline or the public support claim must be narrowed before READY.
```

- [ ] **Step 4: Decide release state**

```text
READY  = all applicable architecture/runtime/reliability/security/engineering/UX/evidence/presentation gates closed.
BLOCKED = any required gate remains unresolved.
```

- [ ] **Step 5: Integrate only after explicit user choice**

```text
Do not merge to main, tag, or publish a release automatically.
Present the verified integration/release choices to the user.
```

---

## Program Completion Criteria

The v1.0 program is complete only when:

1. all nine workstreams have dedicated closure evidence;
2. the public repository is internally consistent;
3. exact supported Codex runtime behavior matches the compatibility contract;
4. security residual risks are explicit and no critical unresolved issue is hidden;
5. clean install and representative workflow are independently reproducible;
6. benchmark wording matches measured state;
7. OpenAI-facing assets contain no unsupported claims;
8. exact release-candidate SHA passes required deterministic CI and runtime acceptance;
9. the final release checklist contains one evidence-backed `READY` or `BLOCKED` decision.
