# CEK v1.0 Skill and Agent Stocktake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prove that every shipped CEK skill, orchestrator reference role, and native subagent has a distinct purpose, correct routing boundary, and explicit evidence/output contract without catalog-size-driven duplication.

**Architecture:** Treat three asset classes separately: shipped skills (`skills/*/SKILL.md`), orchestrator reference roles (`skills/orchestrator/references/roles/*.md`), and runtime-native subagents (`.codex/agents/*.toml`). Add machine-readable inventory/relationship contracts so docs and routing cannot accidentally collapse these distinct concepts.

**Tech Stack:** Markdown skills/reference roles, TOML subagents, Python 3.11 `unittest`, JSON asset inventory.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- A reference role is not automatically a runtime-native subagent.
- A native subagent is not automatically an always-visible skill.
- New assets require a real workflow/context/review gap and must not be added for parity/count marketing.
- Maintainer-local Codex skills remain operator tooling unless independently admitted into CEK.
- Every shipped asset must have a discoverable owner/purpose, activation boundary, expected output/evidence, mutation boundary, and overlap rationale.
- Removing/merging an asset requires regression evidence that its covered workflow remains intact.

---

### Task 1: Add a Canonical Asset Inventory

**Files:**
- Create: `release_contracts/assets.json`
- Create: `tests/test_asset_contract.py`

**Interfaces:**
- Produces: machine-readable records with `id`, `kind`, `path`, `purpose`, `activation`, `output_contract`, `mutation`, `overlap`.
- `kind` is one of `skill`, `reference-role`, `native-subagent`.

- [ ] **Step 1: Write failing inventory tests**

Tests must dynamically discover:

```python
skills = sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md"))
roles = sorted(p.stem for p in (ROOT / "skills/orchestrator/references/roles").glob("*.md"))
agents = sorted(p.stem for p in (ROOT / ".codex/agents").glob("*.toml"))
```

The JSON inventory must contain exactly one record for every discovered path and no record whose path does not exist.

Each record must have non-empty `purpose`, `activation`, `output_contract`, `mutation`, and `overlap` strings.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_asset_contract -v
```

Expected: FAIL because `release_contracts/assets.json` does not exist.

- [ ] **Step 3: Create the inventory from actual repository assets**

Populate all current shipped skills, all current reference roles, and all current native subagents. Do not invent assets that are only present in the maintainer's local Codex installation.

- [ ] **Step 4: Run GREEN**

```bash
python -m unittest tests.test_asset_contract -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add release_contracts/assets.json tests/test_asset_contract.py
git commit -m "test: add CEK asset inventory contract"
```

---

### Task 2: Make Reference-Role vs Native-Subagent Routing Explicit

**Files:**
- Modify: `skills/orchestrator/SKILL.md`
- Modify as needed: `workflows/*.md`
- Modify: `tests/test_asset_contract.py`
- Existing validation: `tests/validate_content.py`

**Interfaces:**
- Consumes: canonical inventory from Task 1.
- Produces: routing language that explicitly distinguishes instruction references from actual runtime-spawned agents.

- [ ] **Step 1: Add a routing-boundary section to the orchestrator**

Required wording concept:

```markdown
## Reference roles vs native subagents

Reference roles under `references/roles/` are lightweight operating contracts loaded into the parent context. They are not proof that a separate agent ran.

Native subagents under `.codex/agents/` are runtime-isolated workers. Use them only when isolation, independent review, or a bounded execution lane has a concrete benefit, and only claim delegation when the runtime actually spawned them.
```

- [ ] **Step 2: Add tests that every backticked primary/companion reference role used by the orchestrator exists under `references/roles/` unless the text explicitly labels it a native subagent**

The test must fail on typos or deleted role references rather than requiring reference-role names to match native agent names.

- [ ] **Step 3: Add explicit mapping notes where both concepts exist**

Examples that must be reviewed rather than mechanically forced:

```text
architect reference role <-> architect native subagent
security-reviewer reference role <-> security-reviewer native subagent
e2e-runner reference role <-> e2e-runner native subagent
refactor-cleaner reference role <-> refactor-cleaner native subagent
code-reviewer reference role -> reviewer native subagent when isolated review is required
build-error-resolver reference role -> build-resolver native subagent when isolated execution is useful
planner/tdd-guide/doc-updater may remain parent-context reference roles if no separate native agent is justified
```

- [ ] **Step 4: Run routing contracts**

```bash
python -m unittest tests.test_asset_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

### Task 3: Review Every Shipped Skill for Trigger Scope and Overlap

**Files:**
- Inspect/Modify: `skills/*/SKILL.md`
- Test: `tests/test_domain_skills.py`, `tests/test_asset_contract.py`

**Interfaces:**
- Produces: narrow activation descriptions and documented overlap rules for all shipped skills.

- [ ] **Step 1: For each skill, complete this review record in `release_contracts/assets.json`**

```text
Unique gap closed:
Activation condition:
What should not trigger it:
Required output/evidence:
Mutation authority:
Overlap/precedence:
Why it deserves a shipped skill rather than a reference section:
```

- [ ] **Step 2: Tighten any broad skill whose activation substantially overlaps another**

Use TDD/content-contract first: add a failing contract asserting the desired routing distinction, then minimally revise the SKILL text.

- [ ] **Step 3: Run skill contracts**

```bash
python -m unittest tests.test_domain_skills -v
python -m unittest tests.test_asset_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

### Task 4: Review Every Native Subagent Contract

**Files:**
- Inspect/Modify: `.codex/agents/*.toml`
- Test: `tests/test_agent_contract.py`, `tests/test_asset_contract.py`

**Interfaces:**
- Produces: native subagent records with explicit purpose, input boundary, expected evidence/output, mutation authority, and completion semantics.

- [ ] **Step 1: Review all current native subagents**

Current expected set is dynamically discovered from `.codex/agents/*.toml`; do not hard-code a permanent count target.

- [ ] **Step 2: Add contract assertions for required behavioral concepts**

Every native agent must have enough configuration/instructions to answer:

```text
what it does
when the parent should use it
what evidence/output it owes the parent
what it may change
when it is done
```

- [ ] **Step 3: Run native-agent tests**

```bash
python -m unittest tests.test_agent_contract -v
python -m unittest tests.test_asset_contract -v
```

Expected: PASS.

---

### Task 5: Reject Unjustified Local-Skill Import

**Files:**
- Modify: `docs/architecture.md` or contributor guidance only if needed
- Modify: `CONTRIBUTING.md`
- Test: `tests/test_asset_contract.py`

**Interfaces:**
- Produces: an explicit skill-admission rule for future contributions.

- [ ] **Step 1: Add admission checklist to contributing guidance**

A proposed new skill/agent must provide:

```text
workflow gap
activation boundary
overlap analysis
context-cost rationale
tests/eval story
maintenance owner
public evidence impact
```

- [ ] **Step 2: State that maintainer-local development skills are not automatically shipped**

This prevents hidden dependency creep.

- [ ] **Step 3: Run contracts**

```bash
python -m unittest tests.test_asset_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

### Task 6: Independent Stocktake Review and Closure

- [ ] **Step 1: Fresh reviewer examines all three asset classes separately**

Reviewer must identify any duplicated purpose, unclear activation, unjustified native isolation, or reference role falsely described as a separately executed agent.

- [ ] **Step 2: Resolve major findings with focused contracts**

Do not delete/merge assets without proving the affected workflow remains covered.

- [ ] **Step 3: Final verification**

```bash
python -m unittest tests.test_asset_contract -v
python -m unittest tests.test_agent_contract -v
python -m unittest tests.test_domain_skills -v
python tests/validate_content.py
git status --short
git rev-parse HEAD
```

Expected: PASS, clean tree, exact reviewed SHA.

---

## Completion Criteria

The stocktake closes when all real repository skills/reference roles/native subagents are represented exactly once in the inventory, routing explicitly distinguishes parent-context roles from spawned agents, every asset has a narrow purpose/output/mutation/overlap contract, no local-only skill is a hidden dependency, and all asset/content contracts pass.