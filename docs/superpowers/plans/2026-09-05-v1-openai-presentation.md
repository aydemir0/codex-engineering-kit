# CEK v1.0 OpenAI-Ready Presentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the verified CEK repository into a reviewer-first public package with a 30-second explanation, reproducible demo, architecture visual, evidence navigation, and complete current OpenAI Showcase submission copy without implied endorsement.

**Architecture:** Build presentation only from closed workstream evidence. Keep three depths: 30-second README surface, 5-minute architecture/demo path, and deep evidence/release docs. Treat OpenAI submission/distribution routes as external surfaces that must be re-verified immediately before submission.

**Tech Stack:** Markdown, Mermaid/source-controlled diagram, public image asset, GitHub repository metadata, OpenAI Showcase form requirements, current OpenAI plugin documentation.

**Spec:** `docs/superpowers/specs/2026-09-05-v1-openai-ready-product-architecture-design.md`

## Global Constraints

- CEK remains an independent project; no wording/design may imply OpenAI partnership, certification, support, or endorsement.
- Every capability sentence must map to current evidence or be explicitly labeled limited/planned.
- Do not call CEK an official "Everything Claude Code for Codex" port; attribution may explain inspiration without copying identity.
- Do not claim universal public Plugin Directory submission unless an official self-serve path for the maintainer is verified at submission time.
- Current official OpenAI documentation allows skills-only plugins and workspace publication but states workspace publication is not public-directory publication.
- Cover image must be owned by the submitter or used with permission and must have a public URL before Showcase submission.
- Demo must be reproducible from the public repository and may not depend on private/local-only skills.

---

### Task 1: Add Submission/Presentation Contracts

**Files:**
- Create: `tests/test_submission_contract.py`
- Create later: `docs/submission/openai-showcase.md`, `docs/submission/plugin-distribution.md`, `docs/demo/v1-demo.md`

**Interfaces:**
- Produces: deterministic presence/length/claim checks for OpenAI-facing copy.

- [ ] **Step 1: Write failing tests**

The test suite must require `docs/submission/openai-showcase.md` to contain structured fields for:

```text
project type
Codex used to build project
other coding agent used
tech stack
use cases
capability
OpenAI models/APIs
other models/APIs
building process
public GitHub URL
hosted URL or explicit N/A
setup steps
title
tagline
description
author display name
cover image URL/status
```

Enforce current Showcase form maxima where content is finalized:

```text
use cases <= 255
capability <= 1000
OpenAI models/APIs <= 500
other models/APIs <= 255
building process <= 500
setup steps <= 500
title <= 255
tagline <= 255
description <= 1000
author display name <= 500
```

Tests must reject `official OpenAI`, `OpenAI-certified`, `OpenAI endorsed`, and `partnered with OpenAI` unless the phrase is inside an explicit negation explaining independence.

- [ ] **Step 2: Run RED**

```bash
python -m unittest tests.test_submission_contract -v
```

Expected: FAIL because submission/demo files do not yet exist.

---

### Task 2: Rebuild README for the Three-Depth Reviewer Journey

**Files:**
- Modify: `README.md`
- Test: `tests/test_submission_contract.py`, `tests/test_quickstart_contract.py`, `tests/test_architecture_contract.py`, `tests/test_release_contract.py`

**Interfaces:**
- Consumes: closed truth/runtime/workflow/security/stocktake/benchmark/install evidence.
- Produces: concise top-level reviewer path without removing deep evidence links.

- [ ] **Step 1: Structure README top section in this order**

```markdown
# Codex Engineering Kit
one-sentence evidence-bound value proposition
independent-project status

## Why CEK
problem -> solution -> differentiator

## What happens in one engineering loop
small architecture/flow visual

## Quick start
proven clean-install path

## Evidence status
compact current support/limitations table

## Demo
link to reproducible demo

## Architecture / Security / Benchmark / Release evidence
links to deep docs
```

Keep existing useful technical sections below or consolidate without losing evidence boundaries.

- [ ] **Step 2: Make the first screen understandable without ECC knowledge**

The value proposition must stand alone. ECC attribution belongs later under attribution/history, not as the primary explanation of CEK.

- [ ] **Step 3: Run public-surface tests**

```bash
python -m unittest tests.test_submission_contract -v
python -m unittest tests.test_quickstart_contract -v
python -m unittest tests.test_architecture_contract -v
python -m unittest tests.test_release_contract -v
python tests/validate_content.py
```

Expected: PASS after later submission files exist; at this task, README-specific tests must pass.

---

### Task 3: Create a Current Architecture Visual and Reproducible Demo Script

**Files:**
- Create: `docs/assets/cek-v1-architecture.mmd`
- Create: `docs/demo/v1-demo.md`
- Later create/render a public cover/demo image asset from the same truthful architecture/UX story.

**Interfaces:**
- Produces: one source-controlled architecture diagram and one fixed demo sequence.

- [ ] **Step 1: Create architecture source**

Diagram must show:

```text
User task
-> native plugin entry
-> orchestrator
-> reference role OR native subagent boundary
-> progressive skill/domain pack
-> hooks + bounded state
-> verification/evals
-> release evidence
```

It must visually distinguish reference roles from actually spawned native subagents.

- [ ] **Step 2: Write `docs/demo/v1-demo.md`**

Required sections:

```markdown
# CEK v1 Demo
## Environment identity
## Clean install
## Representative task
## Expected RED
## CEK routing/plan
## Implementation
## Independent review
## GREEN + verification
## Evidence inspection
## Limitations shown honestly
## Cleanup
```

All commands come from the closed clean-install/core-workflow evidence.

- [ ] **Step 3: Dry-run the script from a disposable environment**

Any step that cannot be reproduced becomes a blocker or is removed from the demo.

---

### Task 4: Prepare Current OpenAI Showcase Submission Copy

**Files:**
- Create: `docs/submission/openai-showcase.md`
- Test: `tests/test_submission_contract.py`

**Interfaces:**
- Produces: copy-ready fields matching the current official Showcase form at `https://openai.com/form/showcase-submission/`.

- [ ] **Step 1: Re-open the official form immediately before finalizing copy**

Verify field names/limits have not changed. The 2026-09-05 verified form explicitly accepts public apps, demos, and open-source projects and asks whether Codex was used to build the project.

- [ ] **Step 2: Fill every required field from repository evidence**

Rules:

```text
Codex build-process answer names exactly how local Codex and ChatGPT were used.
OpenAI APIs/models field uses N/A if CEK itself does not depend on an API/model at runtime; do not invent API usage.
Hosted URL may be N/A when public GitHub is supplied and no hosted demo exists.
Setup steps must match the clean-install evidence.
Tagline and description must not exceed the evidence-bound product claim.
```

- [ ] **Step 3: Run submission contract**

```bash
python -m unittest tests.test_submission_contract -v
```

Expected: PASS including length limits and no implied endorsement.

---

### Task 5: Document Plugin Distribution Without Inventing a Public Submission Path

**Files:**
- Create: `docs/submission/plugin-distribution.md`
- Test: `tests/test_submission_contract.py`

**Interfaces:**
- Produces: current, sourced distribution strategy for local/plugin/workspace/public surfaces.

- [ ] **Step 1: Re-check official OpenAI plugin documentation immediately before submission**

Source: `https://help.openai.com/en/articles/20001256/` or its current canonical successor.

Current verified facts on 2026-09-05:

```text
plugins may contain skills only;
Plugin Directory exists across ChatGPT/Codex surfaces subject to rollout/account/workspace;
workspace members may share/publish owned plugins when permitted;
workspace-directory publication does not publish to the universal public directory;
OpenAI Verified is a selected-developer review program, not a self-awarded badge.
```

- [ ] **Step 2: Document only routes actually available to the maintainer**

If no universal-public submission control is available, record it as an external distribution blocker/unknown and proceed with GitHub + Showcase rather than claiming public-directory publication.

---

### Task 6: Create Cover Image and Demo Media

**Files:**
- Create public visual asset/source under `docs/assets/` or another repository-owned public path.
- Update: `docs/submission/openai-showcase.md` with the final public cover URL.

**Interfaces:**
- Produces: owned visual representing CEK's most important value rather than decorative branding.

- [ ] **Step 1: Use a truthful visual concept**

Preferred concept:

```text
Codex task -> orchestration -> isolated review -> verification -> evidence
```

Do not use OpenAI logos or visual treatment that suggests official status unless brand rules explicitly permit the exact usage.

- [ ] **Step 2: Verify public accessibility and ownership**

The Showcase cover URL must be publicly fetchable and the submitter must own/have permission for it.

- [ ] **Step 3: Record demo media link if available**

The demo may be a short video/GIF, but the repository demo script remains the reproducible source of truth.

---

### Task 7: Fix External GitHub Metadata Blocker

**Files:**
- External GitHub repository metadata; no source file substitutes for this check.

- [ ] **Step 1: Set repository description to evidence-bound wording through a supported admin UI/tool**

Required description unless later evidence justifies a different tested wording:

```text
Evidence-bound engineering workflows for OpenAI Codex.
```

- [ ] **Step 2: Re-fetch repository metadata and verify exact description**

Do not close the blocker based on a source README edit.

---

### Task 8: Final Presentation Review

- [ ] **Step 1: 30-second review**

A fresh reviewer must understand what CEK is, why it matters, current evidence status, and how to try it without scrolling through implementation history first.

- [ ] **Step 2: 5-minute review**

Reviewer can reach architecture, demo, security, benchmark, compatibility, and claim-evidence docs quickly.

- [ ] **Step 3: Deep review**

All public claims trace to repository evidence; limitations are visible rather than buried.

- [ ] **Step 4: Run final presentation contracts**

```bash
python -m unittest tests.test_submission_contract -v
python -m unittest tests.test_quickstart_contract -v
python -m unittest tests.test_architecture_contract -v
python -m unittest tests.test_release_contract -v
python tests/validate_content.py
```

Expected: PASS.

---

## Completion Criteria

Presentation closes when README works at 30-second/5-minute/deep levels, architecture/demo are reproducible and truthful, Showcase copy matches current official fields and limits, plugin distribution wording matches current official availability, cover image is owned/public, external GitHub description is verified, and no OpenAI-facing copy exceeds closed evidence.