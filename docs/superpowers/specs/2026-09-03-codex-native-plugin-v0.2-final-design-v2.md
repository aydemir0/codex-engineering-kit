# Codex Engineering Kit v0.2 — Final Design v2

Status: final design candidate after local Codex audit, Claude adversarial review, Gemini research, and direct reconciliation against current OpenAI documentation. Implementation remains blocked until the owner reviews and approves this file.

This document supersedes the earlier v0.2 design files where they differ.

## 1. Goal

Build a first-class Codex engineering plugin that reaches capability parity with the useful engineering ideas demonstrated by mature Claude Code setups while implementing them through native Codex primitives rather than emulating Claude behavior.

Capability parity is not file-for-file parity.

The release claim must remain evidence-bound:

> Codex Engineering Kit is a Codex-native engineering workflow plugin combining reusable skills, custom subagents, trusted lifecycle hooks, executable verification and evals, review-gated learning, bounded parallelism, safe MCP guidance, and cross-platform automation.

The project must not claim OpenAI or Anthropic endorsement.

## 2. Evidence hierarchy

When sources disagree, decisions follow this order:

1. current official OpenAI documentation and first-party OpenAI source samples
2. reproducible behavior on declared local Codex versions
3. repository tests and CI evidence
4. upstream project behavior and third-party engineering references
5. model-generated research reports

Model-generated reports are research leads, not authority.

No public capability claim may be based only on a model summary.

## 3. Tested-against version window

The initial compatibility pair is:

- terminal-resolved Codex CLI: `0.147.0`
- Codex Desktop bundled CLI: `0.152.0`

Public documentation must state:

> v0.2 is designed and acceptance-tested against Codex CLI 0.147.0 and Codex Desktop's bundled 0.152.0 runtime. Behavior outside this tested window is not guaranteed until separately verified.

The project must maintain a compatibility matrix. Newer Codex releases are not silently assumed compatible.

Do not upgrade the 0.147.0 terminal baseline until its acceptance evidence has been captured.

## 4. Source evidence required before implementation claims

Current official source URLs used by this design:

- Hooks: `https://developers.openai.com/codex/hooks`
- Subagents: `https://developers.openai.com/codex/subagents`
- Plugins: `https://developers.openai.com/codex/plugins`
- Worktrees: `https://learn.chatgpt.com/docs/environments/git-worktrees`
- First-party plugin sample/spec: `https://github.com/openai/codex/tree/main/codex-rs/skills/src/assets/samples/plugin-creator`

Key official hook behaviors used by this design:

- matching hooks from multiple files all run
- multiple matching command hooks for one event may start concurrently
- plugin hooks load alongside user/project/managed hooks
- enabled plugins default to `hooks/hooks.json` discovery unless the manifest overrides it
- `SessionStart.source` may be `startup`, `resume`, `clear`, or `compact`
- `SessionStart` may add developer context
- `PreToolUse` may deny supported local tool calls before execution
- `PreToolUse` may rewrite supported input with `permissionDecision = "allow"` and `updatedInput`
- `permissionDecision = "ask"` is not currently supported
- `SessionEnd` is synchronous and has a short timeout budget
- model-visible hook output is bounded and oversized output spills to a file/preview

These statements still require local acceptance for our declared 0.147.0/0.152.0 window before being promoted from platform capability to project-supported behavior.

## 5. Raw local evidence gate

The existing local Codex audit establishes environment facts, but it is not a substitute for raw command evidence.

Before the v0.2 spec is approved for implementation, capture and retain sanitized raw output for at least:

```text
codex --version
codex plugin list --json
codex plugin marketplace list --json
codex plugin marketplace add --help
codex features list
```

The raw capture must record which binary produced each result when terminal and Desktop runtimes differ.

Do not commit secrets, auth tokens, MCP environment values, or private session data. If raw output contains personal plugin names or machine-specific paths, keep the original outside the repository and commit only a sanitized evidence transcript plus a hash of the original local capture.

## 6. Native Codex contracts

### Plugin

- native manifest: `.codex-plugin/plugin.json`
- repo-local marketplace: `.agents/plugins/marketplace.json`
- personal marketplace: `~/.agents/plugins/marketplace.json`
- locally verified CLI family: `codex plugin ...`
- interactive plugin browser is acceptance-tested separately; do not infer a slash command from binary strings

### Skills

Bundled skills remain under `skills/<name>/SKILL.md` with narrow descriptions and progressive disclosure.

### Custom subagents

Project agents live under `.codex/agents/*.toml`.

Required portable fields are treated as:

- `name`
- `description`
- `developer_instructions`

Do not hard-code a model unless a role demonstrably requires one.

### Hooks

v0.2 actively ships handlers for:

- SessionStart
- SessionEnd
- PreToolUse
- PostToolUse
- PreCompact
- PostCompact
- SubagentStart
- SubagentStop

Other documented hook events remain compatibility surfaces, not required active handlers.

## 7. Open risk register

### RISK-001 — Plugin manifest `hooks` field inconsistency

OpenAI's current Hook documentation says plugin-bundled hooks may be declared through a manifest `hooks` entry or discovered from the default `hooks/hooks.json` path. A first-party plugin-creator sample/spec has contained contradictory validation guidance around the manifest field.

Decision for v0.2:

- ship `hooks/hooks.json`
- rely on default plugin hook discovery first
- omit explicit manifest `hooks` until acceptance proves the override behavior on both 0.147.0 and 0.152.0
- add a dedicated compatibility test for explicit manifest `hooks`

Status: OPEN until both baselines pass.

### RISK-002 — Runtime version skew

Terminal 0.147.0 and Desktop 0.152.0 may differ in plugin, hook, subagent, cache, or worktree behavior.

Mitigation:

- compatibility matrix
- disposable `CODEX_HOME`
- version recorded in every acceptance artifact
- no compatibility claims outside tested versions

Status: OPEN by design.

### RISK-003 — Python runtime dependency

Core v0.2 hook/runtime logic is planned in Python 3 standard library. Python availability is therefore an explicit prerequisite for hook-dependent features unless later replaced by a packaged runtime.

Mitigation:

- `python3` on macOS/Linux
- `py -3` Windows override
- startup prerequisite check
- skills remain usable even if hook-dependent features are unavailable

Status: ACCEPTED LIMITATION for v0.2.

## 8. Repository architecture

```text
codex-engineering-kit/
├── .codex-plugin/plugin.json
├── .agents/plugins/marketplace.json
├── .codex/agents/*.toml
├── hooks/
│   ├── hooks.json
│   └── scripts/*.py
├── runtime/*.py
├── skills/
│   ├── orchestrator/
│   ├── verification-loop/
│   ├── eval-harness/
│   ├── continuous-learning/
│   ├── software-architecture/
│   ├── concurrency-performance/
│   ├── backend-patterns/
│   └── frontend-patterns/
├── verification/
├── evals/
├── workflows/
├── rules/
├── mcp/
├── tests/
└── docs/
```

Workspace runtime state lives under gitignored `.codex-kit/` and is bounded, versioned, and sensitivity-filtered.

## 9. Subagent model

Read-only agents:

- explorer
- architect
- reviewer
- security-reviewer
- docs-researcher

Controlled write agents:

- build-resolver
- e2e-runner
- refactor-cleaner

Rules:

- read-heavy delegation first
- no duplicate research agents
- bounded concurrency
- one write agent per working tree
- no two write agents edit the same worktree concurrently
- return summaries/evidence, not unbounded raw logs

Project example default:

```toml
[agents]
max_concurrent_threads_per_session = 4
```

This is a project default, not a Codex product limit.

## 10. Hook behavior

### SessionStart

- detect repository, branch, and worktree identity
- load bounded checkpoint state
- surface unresolved verification state
- handle `source = "compact"`
- never inject full transcripts

Target project-generated context: approximately 1,500 tokens or less. This target is ours, not the product maximum.

### SessionEnd

- deterministic snapshot only
- no model call
- no expensive repository scan
- no skill generation

### PreToolUse

- deny a narrow deterministic destructive-command set
- add context for generated/vendor/managed files
- reject obvious secret-handling mistakes where deterministic
- rewrite only when a safe exact rewrite is known

Hooks are guardrails, not a sandbox.

### PostToolUse

- record bounded execution evidence
- preserve real result/exit information when available
- never infer success merely from invocation

### Compaction

`PreCompact` persists minimal continuation state. `PostCompact` records the transition. `SessionStart(source="compact")` restores the minimum state needed to continue.

### Subagent lifecycle

Record role, scope, agent id where exposed, start/stop state, and evidence/result location. Raw child transcripts are not the stable data contract.

## 11. Worktree lifecycle — normative design

v0.2 does not build a custom worktree engine. It supports two explicit modes.

### Mode A — Codex-managed worktree

Preferred for Desktop acceptance and user-facing parallel chats.

Lifecycle:

1. user/root coordinator starts an independent write task in Worktree mode
2. Codex creates a managed worktree, normally under `$CODEX_HOME/worktrees`
3. the task runs in the detached worktree or creates a branch there when ready
4. verification runs inside that worktree
5. successful work is either pushed as its own branch/PR or handed off to Local
6. Codex-managed cleanup follows product lifecycle; the project records only the worktree identity and result

### Mode B — CLI/manual Git worktree

Used for deterministic CI/dev tests and flows where Desktop-managed worktrees are unavailable.

Creation contract:

```text
git worktree add --detach <path> <base-sha>
```

When a branch is required, create a unique branch for that worktree after isolation is established.

Integration contract:

- each write track produces commits on its own branch
- root coordinator reviews and verifies the branch before integration
- integration into the target branch occurs through normal Git merge/rebase/cherry-pick policy chosen by the repository, not by a hidden automatic merge
- merge conflicts stop automation; the root coordinator/user resolves or delegates the conflict explicitly
- no agent guesses a semantic conflict resolution without review

Cleanup contract:

- delete only worktrees created by the current fixture/workflow
- require clean or already-captured state before removal
- remove with `git worktree remove <path>`
- run `git worktree prune` only for stale metadata after confirming no live worktree depends on it
- orphaned test worktrees are detected by fixture metadata plus `git worktree list --porcelain`
- CI teardown attempts cleanup even after test failure

Safety invariant:

> No two write agents may share one worktree, and no integration proceeds while the source worktree has uncommitted changes that are not explicitly captured.

## 12. Verification engine

Cross-platform Python engine, initially supporting:

- Node/TypeScript
- Python
- generic repositories

Every step records command, exit code, duration, and status: passed, failed, skipped, unavailable.

Skipped never becomes passed.

Node manager resolution:

1. explicit project setting
2. `packageManager`
3. lockfile
4. available manager
5. npm fallback only when valid

Initial managers: npm, pnpm, yarn, bun.

Verification documentation explicitly warns that repository test/build scripts execute project-authored code under current Codex/user permissions.

## 13. Executable eval harness

Two modes:

- offline deterministic CI
- authenticated Codex/`codex exec` acceptance

Eval classes:

- capability
- regression
- pressure

Initial pressure cases:

- unsupported performance claim
- unbounded concurrency
- destructive shell shortcut
- skip-tests-and-ship
- secret-in-repository

## 14. Context-efficiency benchmark protocol

The project may not use the word `lean` as a measured capability until this protocol has run.

### Compared configurations

A. naive always-loaded engineering instructions

B. progressive-disclosure skill routing

C. native isolated subagent delegation

### Task set

Use at least five representative tasks, fixed before running the benchmark:

1. small bug diagnosis in a Node/TypeScript fixture
2. API/backend design review requiring `backend-patterns`
3. React/Next review requiring `frontend-patterns`
4. concurrency/performance pressure scenario
5. repository-wide review that benefits from explorer + reviewer delegation

The fixtures, prompts, expected outputs/invariants, and repository commit SHAs are pinned.

### Sample count

Minimum initial protocol:

- 5 tasks
- 3 repeated runs per configuration per task
- 45 total runs

More runs may be added if variance is high.

### Model control

- use the same model and reasoning setting for A/B/C within one benchmark campaign
- record exact model slug/runtime version
- do not compare across different model versions as if configuration alone caused the difference

### Measurements

Primary:

- total input tokens
- total output tokens
- cached input tokens where exposed
- total tokens per completed workflow
- wall-clock duration
- pass/fail against task invariants

Secondary:

- parent-thread context growth
- subagent token usage where exposed
- number of tool calls

### Token source hierarchy

1. runtime/API usage fields when Codex exposes them
2. exported structured run metadata
3. tokenizer estimate only when actual usage is unavailable, clearly labeled `estimated`

Do not mix measured and estimated token values in one aggregate without marking them.

### Reporting

Report median plus range for the first small sample. Do not claim statistical significance from 3 repeats. Any public efficiency claim must name the benchmark task set, model, Codex version, sample size, and whether tokens were measured or estimated.

## 15. Continuous learning

Flow remains:

```text
session evidence
→ candidate extraction
→ normalization
→ sensitivity filter
→ duplicate detection
→ confidence/evidence links
→ human review
→ approved reusable pattern
```

Hooks may create candidate pointers. They may not create/install/enable/trust permanent skills automatically.

Adversarial fixtures must include fake keys, credential-like values, private paths, and duplicate observations.

## 16. Domain packs and claim boundary

v0.2 plans two optional skills:

- backend-patterns
- frontend-patterns

Until their content and pressure/regression tests exist, README language must say `planned` or `experimental`. The project must not claim broad day-to-day backend/frontend expertise before those skills are implemented and tested.

## 17. MCP posture

MCP is opt-in and minimal.

- no committed credentials
- no automatic large MCP bundle
- login/auth flows preferred
- malformed provider metadata tested
- auth failure separated from availability failure

Remote/bundled MCP packaging is not required to prove the v0.2 core plugin.

## 18. Claim policy

Until acceptance passes, README must distinguish:

- implemented
- experimentally verified
- planned

Do not claim:

- production-grade without release evidence
- feature parity before parity checklist completion
- lean without benchmark data
- cross-platform before behavior tests on Windows/macOS/Linux
- secure as a blanket property

## 19. Acceptance matrix

v0.2 is complete only when all required gates pass:

- sanitized raw local CLI evidence captured
- plugin manifest validates
- repo-local marketplace validates
- local marketplace plugin installation works
- plugin discovery works on declared baseline
- bundled skill discovery works
- hook trust flow documented and exercised
- eight shipped hooks execute successfully
- destructive PreToolUse fixture is denied
- normal tool fixture is allowed
- SessionStart context remains bounded
- SessionEnd meets timeout budget
- compaction state round-trip works
- one read-only custom agent loads and spawns
- bounded multi-agent review works
- SubagentStart/SubagentStop evidence recorded
- Codex-managed or manual linked-worktree acceptance works without cross-tree writes
- worktree conflict path stops instead of guessing
- worktree cleanup test passes
- learning rejects fake secrets and remains approval-gated
- offline eval runner passes
- authenticated pressure evals are recorded when available
- Node and Python verification fixtures pass
- npm/pnpm/yarn/bun detection tests pass
- Windows, macOS, Linux CI behavior passes
- repository secret scan passes
- release claim/evidence matrix is complete

## 20. Implementation order after approval

1. raw evidence capture and compatibility record
2. plugin manifest + marketplace vertical slice
3. cross-platform runtime foundation
4. hook fixtures and handlers
5. custom subagent vertical slice
6. state/compaction persistence
7. package-manager detection
8. cross-platform verification engine
9. executable eval engine
10. worktree lifecycle fixtures
11. backend/frontend domain packs
12. context-efficiency benchmark harness
13. three-OS CI
14. real Codex acceptance on 0.147.0/0.152.0
15. README/release evidence matrix and submission-readiness review
