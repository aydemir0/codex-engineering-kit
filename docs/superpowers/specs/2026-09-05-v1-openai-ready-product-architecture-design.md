# Codex Engineering Kit v1.0 — OpenAI-Ready Product Architecture Design

Date: 2026-09-05
Status: Design approved in chat; implementation plan not yet written
Branch: `docs/v1-openai-ready-architecture`
Baseline: `a1842b3e63fe15f3bf607833f5d1f43c6b41cb3b`

## 1. Mission

Codex Engineering Kit (CEK) will become a Codex-native engineering operating system: a coordinated set of skills, subagents, hooks, bounded state, verification, evals, domain packs, release contracts, and safe installation/distribution workflows that makes high-discipline software engineering repeatable inside OpenAI Codex.

The working idea may be described informally as "Everything for Codex", but the public product identity remains **Codex Engineering Kit**. CEK must not present itself as an OpenAI product, an Anthropic product, or an official port of Everything Claude Code (ECC).

CEK's differentiation is not raw catalog size. Its differentiator is that Codex-native behavior is implemented against the actual Codex surfaces, verified where possible, and exposed through bounded evidence rather than broad compatibility claims.

## 2. Product doctrine

Every v1.0 capability must satisfy these principles:

1. **Codex-native first.** Prefer native Codex plugin, skill, subagent, hook, and task surfaces over compatibility shims.
2. **Evidence before claims.** Public wording cannot exceed deterministic or runtime evidence.
3. **Progressive disclosure.** Keep the always-visible context small; route to domain knowledge only when the task requires it.
4. **Safe by default.** Destructive or externally visible actions require explicit boundaries and review.
5. **Human authority.** Continuous learning may propose reusable knowledge but cannot silently promote or execute it.
6. **Portable repository truth.** A fresh clone must explain and validate itself without relying on the maintainer's private Codex installation.
7. **No count competition.** New skills or agents are admitted only when they close a demonstrated workflow gap.
8. **Inspectable engineering.** Tests, evidence artifacts, schemas, release contracts, and acceptance records are first-class product surfaces.
9. **Submission-quality UX.** A reviewer should understand the value, install path, architecture, proof, and limitations quickly.
10. **No implied endorsement.** Branding and wording must clearly state that CEK is an independent community project.

## 3. Current v0.2 baseline

The v0.2 branch already establishes a strong foundation:

- native `.codex-plugin` packaging;
- repo-local marketplace metadata;
- eight shipped skills;
- project-local Codex-native subagents;
- default native hook discovery;
- bounded Python hook/runtime helpers;
- local state and compaction continuation;
- verification and eval tooling;
- manual Git-worktree acceptance;
- backend/frontend domain packs;
- a fixed A/B/C benchmark protocol;
- machine-readable release claims and compatibility status;
- deterministic CI on Ubuntu, Windows, and macOS.

The Plan F implementation evidence gate is closed at its proven boundary, but v0.2 remains intentionally blocked from an RC-ready claim because runtime and public-metadata blockers remain open.

### Known documentation drift

`README.md` describes the v0.2 eight-skill/native-hooks/native-subagents surface, while `docs/architecture.md` still describes the older v0.1 six-skill + wrapper lifecycle model. v1.0 treats this type of internal contradiction as a release blocker.

## 4. Competitive position

ECC is a mature multi-harness engineering toolkit with a large catalog of agents and skills and a supported Codex synchronization path. CEK will not try to win by reproducing its catalog count.

CEK instead targets five defensible advantages:

1. **Codex-native architecture** rather than a Claude-first system synchronized into Codex.
2. **Runtime-scoped compatibility evidence** for the exact Codex surfaces CEK claims.
3. **Machine-readable release contracts** that prevent documentation from outrunning proof.
4. **Small-context orchestration** with progressive disclosure and isolated subagent delegation.
5. **Submission-grade transparency** around unsupported, blocked, experimental, and measured states.

The benchmark question is not "Does CEK have more skills?" It is "Does CEK create a more reliable engineering loop in Codex with controlled context cost and verifiable outputs?"

## 5. Target v1.0 architecture

CEK v1.0 is organized into eight layers.

```text
User task
  -> Layer 1: Product entry / plugin discovery
  -> Layer 2: Orchestration and routing
  -> Layer 3: Focused native subagents
  -> Layer 4: Progressive-disclosure skills and domain packs
  -> Layer 5: Hooks, policy guardrails, bounded state
  -> Layer 6: Verification, evals, security and benchmark evidence
  -> Layer 7: Release contracts and compatibility gates
  -> Layer 8: Documentation, demo and OpenAI submission surfaces
```

### Layer 1 — Product entry and plugin discovery

The primary experience is the Codex-native plugin package. Users should not need to copy unrelated configuration fragments merely to understand or try CEK.

Requirements:

- valid plugin metadata;
- deterministic repository-local installation path for development;
- installation validation and clear failure messages;
- skills-only operation must remain possible when no external app is required;
- optional external integrations must never become hidden mandatory dependencies;
- supported runtimes must be named explicitly.

The PowerShell installer remains a secondary toolkit-owned delivery path for owned skill installation and lifecycle management. It must not be confused with the native plugin path.

### Layer 2 — Orchestration and routing

The `orchestrator` remains the front door for complex engineering workflows.

Its responsibilities are limited to:

- classify the task;
- choose a workflow;
- route to the smallest relevant skill set;
- delegate isolated work where a native subagent provides a real context or review benefit;
- preserve explicit approval gates;
- collect verification evidence;
- stop when required evidence is missing.

It must not become a giant always-loaded encyclopedia.

### Layer 3 — Native subagents

Current native subagent roles form the baseline:

- architect;
- build-resolver;
- docs-researcher;
- e2e-runner;
- explorer;
- refactor-cleaner;
- reviewer;
- security-reviewer.

New agents are added only when a distinct context boundary or independent-review need is demonstrated. "One persona per task" is explicitly rejected.

A v1.0 agent contract should define:

- purpose;
- activation conditions;
- allowed inputs;
- expected evidence/output;
- mutation permissions;
- completion criteria;
- parent/child lifecycle expectations.

### Layer 4 — Skills and domain packs

The current eight shipped skills remain the baseline:

- `orchestrator`;
- `continuous-learning`;
- `eval-harness`;
- `verification-loop`;
- `software-architecture`;
- `concurrency-performance`;
- `backend-patterns`;
- `frontend-patterns`.

v1.0 does not set a marketing target for the number of skills.

Skill admission requires all of the following:

1. a real workflow gap;
2. a narrow trigger definition;
3. non-overlap or documented precedence with existing skills;
4. deterministic content/schema checks;
5. a verification or eval story;
6. context-cost consideration;
7. maintainer ownership and update policy.

Broad ecosystems should be implemented as optional domain packs where possible, not always-visible core skills.

### Local operator skills vs shipped CEK skills

The maintainer's local Codex installation may contain additional development skills such as Superpowers workflow skills for planning, TDD, systematic debugging, verification, and branch finishing. These are allowed to help build CEK, but they are **operator tooling**, not CEK dependencies unless they independently pass the CEK skill-admission process.

This distinction prevents the public repository from relying on hidden local capabilities.

### Layer 5 — Hooks, guardrails and bounded state

Hooks provide lifecycle enforcement and evidence collection, not a security sandbox.

v1.0 rules:

- default native hook discovery is the preferred production path until explicit manifest hooks have runtime evidence;
- explicit hook override remains experimental while RISK-001 is unresolved;
- PreToolUse deny/allow behavior must be narrow, deterministic, and regression-tested;
- SessionEnd behavior must have a resolved timeout/lifecycle classification before release claims include it;
- hook logs/evidence must strip secrets, raw session IDs, auth tokens, and unnecessary payload content;
- state schemas must be versioned and bounded;
- `.codex-kit` remains local/ignored unless a specific export format is designed;
- state recovery must fail safely on unknown/incompatible schemas.

### Layer 6 — Verification, evals, security and benchmark evidence

#### Verification

Verification must prefer deterministic proof in this order when available:

1. parser/schema validity;
2. tests and exit codes;
3. repository invariants;
4. runtime acceptance;
5. model-assisted review.

Missing evidence produces PARTIAL/BLOCKED/NOT_RUN, never fabricated success.

#### Evals

Evals must separate:

- capability tests;
- regression tests;
- workflow-quality tests;
- context-efficiency experiments;
- model-assisted judgment.

Model-assisted graders may complement deterministic graders but may not erase a deterministic failure.

#### Security

Security review covers at minimum:

- prompt/instruction injection in reusable assets;
- unsafe shell/tool guidance;
- destructive write paths;
- secrets and credentials;
- local state leakage;
- MCP/app permission boundaries;
- dependency provenance;
- update/install ownership;
- unsafe learned-content promotion;
- plugin metadata and external URL trust.

#### Benchmarking

The current 45-run A/B/C protocol remains the basis for the context-efficiency study:

- A — naive always-loaded;
- B — progressive disclosure;
- C — isolated subagent.

No "lean", token-saving, or context-efficiency marketing claim is allowed until the authenticated campaign is executed, validated, and reproducible enough for public evidence.

### Layer 7 — Release contracts and compatibility gates

The v0.2 claim/compatibility model becomes mandatory for v1.0.

Every major public claim maps to one of:

- IMPLEMENTED;
- VERIFIED;
- LIMITED;
- PLANNED.

Every declared runtime surface maps to one of:

- PASS;
- FAIL;
- BLOCKED;
- NOT_RUN.

v1.0 release gates require:

- docs and machine-readable contracts agree;
- no stale version/count/capability wording;
- exact candidate SHA is tested;
- required CI is green;
- declared runtime acceptance is complete or the claim is narrowed;
- critical security review is complete;
- install/update/uninstall paths are exercised;
- demo steps run from a clean environment;
- benchmark claims match actual benchmark state;
- release notes list limitations explicitly.

### Layer 8 — Documentation, demo and OpenAI submission surfaces

The product must be understandable at three depths.

#### 30-second layer

A reviewer sees:

- what CEK is;
- why it exists;
- one architecture graphic;
- one short demo;
- one install command/path;
- current evidence status.

#### 5-minute layer

A reviewer can understand:

- the engineering loop;
- native plugin/skill/subagent/hook architecture;
- verification and release-contract model;
- security boundaries;
- benchmark method;
- major limitations.

#### Deep technical layer

The repository contains:

- architecture docs;
- compatibility matrix;
- claim-evidence matrix;
- runtime acceptance artifacts;
- benchmark protocol/results;
- security model;
- contribution rules;
- implementation/design history.

## 6. Required user journey for v1.0

A clean reviewer journey should be:

1. Open repository.
2. Understand value from README without prior context.
3. See a short architecture diagram.
4. Install or run the documented development/native plugin path.
5. Confirm the plugin exposes the expected CEK surface.
6. Run one representative engineering workflow.
7. Observe plan -> test -> implement -> review -> verify behavior without hidden dependencies.
8. Inspect generated evidence/state without secrets.
9. Run the documented verification command set.
10. Review compatibility limitations.
11. Watch/read a concise demonstration of a real before/after workflow.

A release candidate fails if this path depends on undocumented maintainer-only state.

## 7. OpenAI submission strategy

CEK targets two complementary submission surfaces.

### A. Open-source / direct-review package

Artifacts:

- public GitHub repository;
- polished README;
- architecture diagram;
- short demo video/GIF;
- clean release/tag;
- release notes;
- evidence matrix;
- benchmark report when measured;
- short technical pitch;
- optional hosted documentation/landing surface if it materially improves evaluation.

### B. OpenAI ecosystem submission package

#### Showcase Gallery

The current OpenAI Showcase submission form explicitly accepts public apps, demos, and open-source projects and asks whether Codex was used to build the project. CEK should prepare every required field in advance, including:

- project type;
- Codex usage/build process;
- stack;
- use cases;
- OpenAI capabilities/models/APIs used, or N/A when not applicable;
- public GitHub or hosted URL;
- setup steps;
- project title;
- tagline;
- project description;
- author display name;
- public cover image.

The submission copy must not imply OpenAI endorsement.

#### Plugin ecosystem

OpenAI's current plugin documentation describes plugins as packages that may include skills, apps, and app templates, and explicitly allows skills-only plugins. CEK should therefore maintain a publication-quality plugin artifact even if it has no external app dependency.

However, the currently verified public documentation distinguishes workspace publication from universal public-directory publication and does not establish a guaranteed self-serve universal-public submission route for every developer. CEK must therefore prepare for public review/distribution without claiming a submission mechanism that has not been verified for the maintainer's account.

## 8. OpenAI-facing story

The project story should be factual and compact:

**Problem:** Coding agents can generate code, but reliable engineering requires repeatable planning, context control, verification, security review, state management, and evidence-bound release discipline.

**Solution:** CEK packages those engineering behaviors as Codex-native skills, subagents, hooks, state helpers, verification/eval tooling, and release contracts.

**Why it is different:** CEK treats compatibility and quality as measured properties rather than marketing adjectives. Unsupported or blocked runtime surfaces remain visibly blocked.

**Why Codex:** CEK is designed around Codex-native plugin, skill, subagent, hook, and task behavior rather than treating Codex as a secondary compatibility target.

## 9. v1.0 quality gates

The project is not submission-ready until all applicable gates below are closed.

### Architecture gate

- one source-of-truth architecture model;
- no v0.1/v0.2/v1.0 contradictions;
- clear component ownership and boundaries;
- no unnecessary always-loaded context.

### Runtime gate

- supported Codex CLI surface verified;
- supported Desktop surface verified or explicitly excluded/narrowed;
- explicit hooks issue resolved or kept out of supported surface;
- SessionEnd classification resolved or excluded;
- parent-wait behavior classified or excluded.

### Reliability gate

- installation path tested from clean state;
- update/uninstall ownership tested where applicable;
- state schema/recovery tested;
- hooks/subagents fail predictably;
- representative workflow acceptance passes.

### Security gate

- threat model reviewed;
- no secrets/private transcripts committed;
- action boundaries documented;
- dependency/provenance review complete;
- learned-content promotion remains human-gated.

### Engineering gate

- focused unit/integration/acceptance suites pass;
- supported repository CI is green;
- release contracts validate;
- no known critical regression hidden by model judgment.

### UX gate

- quick start is copyable and current;
- first useful workflow is obvious;
- failure messages guide the user;
- requirements and limitations are near the install path.

### Evidence gate

- every marketing claim maps to evidence;
- benchmark claims are measured or omitted;
- compatibility claims are exact-runtime scoped;
- stale docs/counts are blocked by tests where practical.

### Presentation gate

- README is reviewer-oriented;
- architecture diagram is current;
- demo asset exists;
- cover image exists;
- Showcase submission answers are prepared;
- concise project pitch exists;
- GitHub repository metadata uses evidence-bound wording.

## 10. What v1.0 will deliberately not do

- clone ECC's catalog for numerical parity;
- claim feature parity with Claude Code/ECC;
- claim blanket cross-platform runtime support from three-OS repository CI;
- treat hooks as a sandbox;
- auto-promote learned instructions;
- commit credentials, raw private transcripts, or machine-local sensitive state;
- make the maintainer's private Codex skills a hidden runtime dependency;
- advertise benchmark improvements before the real campaign exists;
- use OpenAI branding in a way that implies partnership, verification, certification, or endorsement.

## 11. Workstream decomposition

The architecture should be implemented as independent evidence-gated workstreams rather than one giant v1.0 change.

1. **Truth surface reconciliation** — architecture/docs/version/count/metadata consistency.
2. **Runtime closure** — Desktop, explicit hooks, SessionEnd, parent-wait and compatibility decisions.
3. **Core workflow hardening** — orchestration, agents, state, hooks, representative acceptance.
4. **Security hardening** — threat model, scanner/checks, action/state/install boundaries.
5. **Skill/agent stocktake** — justify current assets, remove overlap, admit only proven gaps.
6. **Benchmark execution** — authenticated 45-run campaign and reproducible report.
7. **Clean-install UX** — native plugin onboarding and deterministic smoke validation.
8. **OpenAI-ready presentation** — README hierarchy, diagrams, demo, cover asset, pitch, submission copy.
9. **v1.0 release gate** — exact-SHA final verification and evidence-bound release decision.

Each workstream receives its own implementation plan/tasks, TDD or contract-first verification where applicable, review pass, and closure evidence.

## 12. Development collaboration model

CEK may be built using both ChatGPT and the maintainer's local Codex installation.

Recommended division:

- ChatGPT: architecture, repository-wide consistency, evidence policy, cross-source review, GitHub coordination, submission package.
- Codex local: repository-local implementation, local runtime acceptance, clean install tests, shell/PowerShell execution, Desktop/CLI behaviors unavailable in the ChatGPT harness.
- Independent review pass: use a fresh context/tooling lane to review claims, security, tests, and diffs.

Codex outputs are treated as evidence only when their exact command/runtime/repository SHA and relevant sanitized result are recorded. "Codex said it works" is not a release artifact.

## 13. Success condition

v1.0 succeeds when an OpenAI reviewer or experienced developer can independently conclude, from the public repository and reproducible evidence, that CEK is a serious Codex-native engineering system—not merely a prompt collection or renamed Claude toolkit.

The ideal final impression is:

> CEK makes disciplined Codex engineering repeatable, inspectable, and difficult to overclaim.

## 14. Current external references checked for this design

- OpenAI Showcase Gallery submission form: https://openai.com/form/showcase-submission/
- OpenAI Developer Showcase: https://developers.openai.com/showcase
- OpenAI plugins in ChatGPT and Codex: https://help.openai.com/en/articles/20001256/
- ECC upstream repository/README: https://github.com/affaan-m/ECC
