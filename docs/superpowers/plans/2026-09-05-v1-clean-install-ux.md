# CEK v1.0 Clean-Install UX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a fresh reviewer able to clone CEK, install/discover the native plugin in an isolated Codex profile, run a first useful workflow, verify the result, and clean up without undocumented maintainer state.

**Architecture:** Reuse the existing `plugin_smoke.py` disposable-`CODEX_HOME` acceptance path as the core install proof, add first-run/quick-start contracts around it, and keep the native plugin path separate from the optional PowerShell-owned skill installer.

**Tech Stack:** Codex CLI, `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json`, Python 3.11 acceptance helpers, PowerShell 7 installer lifecycle tests, Markdown docs.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- Native plugin install/discovery is the primary v1 reviewer path.
- The PowerShell skill installer is a separate secondary delivery path and must not be presented as required for native plugin use unless runtime evidence proves otherwise.
- Use disposable `CODEX_HOME`; never require the maintainer's normal Codex profile.
- Quick-start commands must be copyable and correspond to the exact supported runtime surface.
- Failure guidance must distinguish missing Codex/runtime support from CEK packaging failure.
- Cleanup must remove disposable state and must not delete user-owned files.
- README cannot promise Desktop or explicit-hook behavior beyond the runtime-closure matrix.

---

### Task 1: Add a First-Run Documentation Contract

**Files:**
- Create: `tests/test_quickstart_contract.py`
- Modify later: `README.md`
- Read: `.codex-plugin/plugin.json`, `scripts/acceptance/plugin_smoke.py`

**Interfaces:**
- Produces: deterministic checks that the README's primary quick start names requirements, plugin path, verification, compatibility link, and separate PowerShell path.

- [ ] **Step 1: Write failing quick-start tests**

Tests must require README to contain:

```text
Python 3.11+
Codex runtime requirement
native plugin / repo-local marketplace sequence
`docs/release/compatibility-matrix.md`
a verification command
clear statement that the PowerShell installer is a separate delivery path
```

Tests must reject wording that calls three-OS CI blanket runtime compatibility or calls the PowerShell installer mandatory for native plugin use.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_quickstart_contract -v
```

Expected: FAIL only for genuinely missing reviewer-path requirements; do not rewrite already-correct README sections to manufacture work.

---

### Task 2: Re-run Native Plugin Smoke from a Clean Profile

**Files:**
- Use: `scripts/acceptance/plugin_smoke.py`
- Test: `tests/test_plugin_smoke.py`, `tests/test_plugin_contract.py`
- Create sanitized evidence: `docs/research/evidence/codex-v1-clean-install.md`

**Interfaces:**
- Consumes: exact supported Codex executable and final candidate SHA.
- Produces: disposable-profile proof of marketplace registration, pre-install discovery, install/enable, final listing, and cleanup.

- [ ] **Step 1: Run deterministic helper tests**

```bash
python -m unittest tests.test_plugin_smoke -v
python -m unittest tests.test_plugin_contract -v
```

Expected: PASS.

- [ ] **Step 2: Run real smoke acceptance**

```powershell
$Output = Join-Path ([IO.Path]::GetTempPath()) ('cek-v1-plugin-smoke-' + [guid]::NewGuid() + '.json')
python scripts/acceptance/plugin_smoke.py --codex $env:CEK_CODEX_SUPPORTED --repo . --output $Output
```

Expected: PASS and JSON artifact outside the repository.

- [ ] **Step 3: Inspect required checks**

The local artifact must prove disposable Codex home use/removal, expected CEK plugin identity, pre-install discovery, final installed/enabled state, and exact runtime version.

- [ ] **Step 4: Write sanitized evidence summary**

Commit only OS/runtime version, exact candidate SHA, plugin version, bounded command sequence/result, cleanup result, raw artifact SHA-256, and limitations. Do not commit the raw profile path.

---

### Task 3: Prove a First Useful Workflow After Install

**Files:**
- Consume: representative workflow fixture/evidence from `2026-09-05-v1-core-workflow-hardening.md`
- Modify README only after proof.

**Interfaces:**
- Produces: one short post-install command/prompt path that exercises CEK rather than merely proving it appears in `plugin list`.

- [ ] **Step 1: In the same disposable-reviewer model, run the representative fixture or another fixed shipped first-run fixture**

Required result:

```text
plugin installed -> CEK surface discovered -> one evidence-first engineering task -> deterministic verification result
```

- [ ] **Step 2: Record exact user-visible success path and failure path**

Failure guide must distinguish:

```text
Codex executable/version missing
marketplace registration failure
plugin discovery failure
plugin install failure
workflow verification failure
unsupported runtime surface
```

---

### Task 4: Rewrite README Quick Start Around the Proven Journey

**Files:**
- Modify: `README.md`
- Test: `tests/test_quickstart_contract.py`, `tests/test_release_contract.py`, `tests/test_architecture_contract.py`

**Interfaces:**
- Consumes: clean-install and first-workflow evidence.
- Produces: a reviewer-oriented copyable quick start with nearby requirements and limitations.

- [ ] **Step 1: Keep the primary path concise**

Required ordering:

```markdown
Requirements
Clone
Native plugin discovery/install
First useful workflow
Verify
Compatibility/limitations
Secondary PowerShell installer
```

Do not put benchmark/security deep-dive prose inside the first-run commands.

- [ ] **Step 2: Use only commands proven by the clean-install acceptance**

The existing proven plugin sequence may be included exactly where supported:

```text
codex plugin marketplace add <repo-root> --json
codex plugin marketplace list --json
codex plugin list --available --json
codex plugin add codex-engineering-kit@codex-engineering-kit-dev --json
codex plugin list --json
```

- [ ] **Step 3: Run documentation contracts**

```bash
python -m unittest tests.test_quickstart_contract -v
python -m unittest tests.test_architecture_contract -v
python -m unittest tests.test_release_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

### Task 5: Re-run Secondary PowerShell Installer Lifecycle

**Files:**
- Use/Modify only on failure: `scripts/install.ps1`, package manager implementation
- Test: `tests/Test-Install.ps1`, `tests/test_package_manager.py`

- [ ] **Step 1: Run deterministic package tests**

```bash
python -m unittest tests.test_package_manager -v
```

Expected: PASS.

- [ ] **Step 2: On Windows run installer lifecycle**

```powershell
./tests/Test-Install.ps1
```

Expected: PASS including ownership-safe install/update/uninstall behavior.

- [ ] **Step 3: Ensure README labels this path secondary**

It must not be confused with the native plugin smoke evidence.

---

### Task 6: Independent Reviewer Journey

- [ ] **Step 1: Give a fresh reviewer only the public repository/README**

The reviewer should be able to identify requirements, install path, first useful action, verification, limitations, and uninstall/cleanup boundaries without private instructions.

- [ ] **Step 2: Record any ambiguity as a UX defect**

Fix the smallest documentation/helper issue and add/adjust a contract so the ambiguity does not regress.

- [ ] **Step 3: Final verification**

```bash
python -m unittest tests.test_quickstart_contract -v
python -m unittest tests.test_plugin_smoke -v
python -m unittest tests.test_plugin_contract -v
python -m unittest tests.test_release_contract -v
python tests/validate_content.py
git status --short
git rev-parse HEAD
```

Expected: PASS, clean tree, exact reviewed SHA.

---

## Completion Criteria

Clean-install UX closes when a disposable-profile real smoke passes on the declared runtime, one post-install CEK workflow is proven, README mirrors only proven commands/support, PowerShell remains clearly separate, a fresh reviewer can complete the journey without hidden state, and all quick-start/plugin/release contracts pass.