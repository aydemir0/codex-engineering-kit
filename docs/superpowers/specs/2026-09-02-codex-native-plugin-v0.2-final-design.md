# Codex Engineering Kit v0.2 — Final Codex-Native Plugin Design

Status: final design candidate after local Codex audit, adversarial review, and official-doc reconciliation. Implementation is blocked on user review of this file.

This document supersedes `2026-09-02-codex-native-plugin-v0.2-design.md` where the two differ.

## 1. Goal

Build a first-class Codex engineering plugin that reaches capability parity with the useful engineering ideas demonstrated by mature Claude Code setups while implementing them through native Codex primitives rather than emulating Claude behavior.

The target is capability parity, not file-for-file parity.

The release claim must remain evidence-bound:

> Codex Engineering Kit is a Codex-native engineering workflow plugin combining reusable skills, custom subagents, trusted lifecycle hooks, executable verification and evals, review-gated learning, safe MCP guidance, bounded parallelism, and cross-platform automation.

The project must not claim OpenAI or Anthropic endorsement and must not imply that Everything Claude Code itself was the hackathon-winning submission.

## 2. Evidence hierarchy

When sources disagree, decisions follow this order:

1. current official OpenAI documentation and source samples
2. reproducible behavior on supported local Codex versions
3. repository tests and CI evidence
4. upstream project behavior and third-party engineering references
5. model-generated research reports

Model-generated reports are research leads, never authority.

## 3. Supported Codex baseline

The first compatibility pair is intentionally the user's current environment:

- terminal-resolved Codex CLI 0.147.0
- Codex Desktop bundled CLI 0.152.0

Do not upgrade the 0.147.0 terminal baseline until its acceptance results are captured.

The project must maintain an explicit compatibility matrix. A capability may be documented as supported only when its required path works on the declared baseline or is clearly marked version-specific.

Tests that touch Codex configuration use a disposable `CODEX_HOME`; they do not mutate the user's real profile.

## 4. Native Codex contracts used by v0.2

### Plugins

- native manifest: `.codex-plugin/plugin.json`
- development distribution: local marketplace
- personal marketplace: `~/.agents/plugins/marketplace.json`
- repo/team marketplace: `<repo-root>/.agents/plugins/marketplace.json`
- official interactive plugin browser: `/plugins`
- locally verified CLI family: `codex plugin ...`
- ChatGPT and Codex share the public universal plugin directory

### Skills

Bundled skills remain under `skills/<name>/SKILL.md` and use narrow `name`/`description` metadata for progressive disclosure.

### Custom subagents

Project agents live under `.codex/agents/*.toml`.

Required fields:

- `name`
- `description`
- `developer_instructions`

Portable agent definitions do not hard-code a model unless a role demonstrably needs one. When model and reasoning settings are omitted, Codex can inherit configured defaults or parent settings.

### Hooks

The documented event set is:

- PreToolUse
- PermissionRequest
- PostToolUse
- PreCompact
- PostCompact
- UserPromptSubmit
- SubagentStop
- Stop
- SessionStart
- SubagentStart
- SessionEnd

The local binary also recognizes `Interrupt`, but v0.2 does not depend on it because it is not part of the current public hook table.

Matching hooks from multiple sources compose; v0.2 does not assume plugin hooks shadow user hooks.

Unmanaged hooks require explicit trust. Installing or enabling the plugin does not imply trust in bundled hooks.

## 5. Repository architecture

```text
codex-engineering-kit/
├── .codex-plugin/
│   └── plugin.json
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .codex/
│   ├── agents/
│   │   ├── explorer.toml
│   │   ├── architect.toml
│   │   ├── planner.toml
│   │   ├── reviewer.toml
│   │   ├── security-reviewer.toml
│   │   ├── build-resolver.toml
│   │   ├── e2e-runner.toml
│   │   ├── refactor-cleaner.toml
│   │   └── docs-researcher.toml
│   └── config.example.toml
├── hooks/
│   ├── hooks.json
│   └── scripts/
│       ├── session_start.py
│       ├── session_end.py
│       ├── pre_tool_use.py
│       ├── post_tool_use.py
│       ├── pre_compact.py
│       ├── post_compact.py
│       ├── subagent_start.py
│       └── subagent_stop.py
├── runtime/
│   ├── project_detector.py
│   ├── package_manager.py
│   ├── checkpoint.py
│   ├── state_store.py
│   ├── policy.py
│   ├── evidence.py
│   └── secrets.py
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
│   ├── presets/
│   └── runner.py
├── evals/
│   ├── capability/
│   ├── regression/
│   ├── pressure/
│   ├── fixtures/
│   └── runner.py
├── workflows/
├── rules/
├── mcp/
├── scripts/
├── tests/
└── docs/
```

Workspace runtime state is not committed:

```text
.codex-kit/
├── state.json
├── checkpoints/
├── evidence/
├── learning-candidates/
└── eval-results/
```

`.codex-kit/` is gitignored by default.

## 6. Plugin packaging strategy

The plugin manifest becomes the primary distribution surface. The existing PowerShell installer remains a compatibility/migration fallback until native installation is proven.

The first development manifest stays intentionally minimal:

- name
- semantic version
- description
- skills path
- submission metadata only when required and validated

The plugin will initially rely on Codex's default plugin-hook discovery at `hooks/hooks.json` rather than an explicit manifest `hooks` override. Current official Hook docs support a manifest override, but the current plugin-creator source sample contains contradictory validation notes about that field. We avoid the ambiguity until local acceptance proves the explicit override on both baseline versions.

v0.2 does not require a bundled remote MCP server to prove the core plugin. MCP packaging remains optional and separately acceptance-tested if added.

## 7. Subagent architecture

The v0.1 markdown role references become real Codex custom agents.

### Read-only evidence agents

- explorer: repository and execution-path mapping
- architect: boundaries, alternatives, failure modes
- reviewer: correctness, regressions, missing tests
- security-reviewer: threat-focused analysis
- docs-researcher: version-specific API/documentation verification

These explicitly use `sandbox_mode = "read-only"`.

### Controlled write agents

- build-resolver: narrowly scoped reproducible build fixes
- e2e-runner: test artifacts and reproducible flows
- refactor-cleaner: proven dead-code cleanup with verification

Write-capable roles are used only after evidence exists.

### Concurrency policy

Project example config sets:

```toml
[agents]
max_concurrent_threads_per_session = 4
```

Four is a conservative project default, not a Codex product limit. Users may override it.

Rules:

- parallelize only independent work
- prefer read-heavy delegation
- do not spawn duplicate research agents
- one write agent per working tree
- two write agents never edit the same worktree concurrently
- subagent results return summaries/evidence, not large raw logs

## 8. Hook architecture

v0.2 actively ships handlers for eight lifecycle events:

- SessionStart
- SessionEnd
- PreToolUse
- PostToolUse
- PreCompact
- PostCompact
- SubagentStart
- SubagentStop

PermissionRequest, UserPromptSubmit, and Stop are documented compatibility surfaces but do not need active handlers in v0.2 unless a tested requirement emerges.

### SessionStart

- detect repository/worktree/branch
- load compact checkpoint and unresolved verification state
- inject bounded developer context
- handle `source = "compact"` for continuation after compaction

SessionStart context is capped below the product default where possible; target plugin configuration is approximately 1,500 tokens, and tests must prove the generated context is bounded.

Full transcripts are never injected as persistent state.

### SessionEnd

Official behavior gives SessionEnd a very short timeout. Therefore it only:

- writes a cheap deterministic snapshot
- records pointers to pending learning/eval candidates
- performs no model call
- performs no expensive scan

### PreToolUse

This is a small deterministic guardrail.

It may:

- deny a narrow set of clearly destructive commands
- add context when generated/vendor/managed files are touched
- reject obvious secret-handling mistakes where the pattern is deterministic
- rewrite supported input only when an explicit safe rewrite is known

Canonical deny output uses `permissionDecision = "deny"` with a reason. Rewrites use `permissionDecision = "allow"` with `updatedInput`.

Do not use unsupported `permissionDecision = "ask"` behavior.

PreToolUse is not presented as a complete security boundary.

### PostToolUse

- records bounded evidence for relevant commands and edits
- records exit/result state when available
- never claims a tool succeeded solely because it was invoked
- never pretends it can undo side effects after execution

### PreCompact/PostCompact

PreCompact persists critical continuation state. PostCompact records the transition. `SessionStart(source="compact")` restores only the minimum developer context needed for continuation.

The toolkit does not inspect or rewrite opaque internal compacted items.

### SubagentStart/SubagentStop

Record:

- role
- scope
- start/stop state
- evidence/result location

Use this data to detect duplicate delegation and failed tasks without storing raw subagent transcripts as the stable contract.

## 9. Hook runtime and portability

Core hook/runtime implementation uses Python 3 standard library only.

Hook config uses platform-specific commands where necessary:

- Unix/macOS: `python3 ...`
- Windows: `py -3 ...` through `commandWindows`

Python availability is an explicit runtime prerequisite for hook-dependent v0.2 features. Installation/acceptance documentation must say so plainly.

If Python is unavailable, plugin skills remain conceptually usable but hook-dependent capabilities are unsupported; the project must not silently claim them as active.

PowerShell scripts remain for Windows-friendly migration and v0.1 compatibility, but core v0.2 verification/eval/state logic does not depend on PowerShell.

CI targets:

- ubuntu-latest
- windows-latest
- macos-latest

## 10. State and memory

State is versioned, bounded, and sensitivity-filtered.

No network telemetry is added by the core plugin.

`PLUGIN_DATA` may hold plugin-local cache/compatibility metadata. Project-specific engineering state remains under the workspace `.codex-kit/` directory so it can be deleted independently and inspected by the user.

Full chat transcripts are not a stable storage interface. Transcript paths may be used as ephemeral evidence only where the official hook contract provides them and tests prove the behavior.

## 11. Continuous learning

Learning remains review-gated:

```text
session evidence
→ candidate extraction
→ normalization
→ secret/sensitivity filter
→ duplicate detection
→ confidence + evidence links
→ human review
→ approved reusable pattern/skill
```

A hook may create a candidate pointer; it may not create, install, enable, or trust a permanent skill.

Required adversarial tests include fake API keys, credential-like strings, private paths, and duplicated observations.

## 12. Verification engine

The PowerShell verifier becomes a Python cross-platform engine.

Initial presets:

- Node/TypeScript
- Python
- generic repository

Each step records:

- command
- exit code
- duration
- passed/failed/skipped/unavailable

Skipped is never passed.

Verification warns that project test/build scripts execute repository-authored code with the user's current sandbox/permissions; verification is not passive inspection.

Node package-manager resolution order:

1. explicit project setting
2. `packageManager` in package.json
3. lockfile detection
4. available manager
5. npm fallback only when valid

Initial managers: npm, pnpm, yarn, bun. Conflicting lockfiles produce a warning.

## 13. Executable eval harness

Two modes:

### Offline deterministic mode

Runs in ordinary CI without an authenticated Codex account. It validates fixtures, policy outputs, parser contracts, state transitions, and expected invariants.

### Authenticated agent mode

Uses real Codex/`codex exec` for representative capability and pressure scenarios when credentials/product access are available.

Eval classes:

- capability
- regression
- pressure

Initial pressure scenarios:

- unsupported performance-improvement claim
- unbounded concurrency pressure
- destructive shell pressure
- skip-tests-and-ship pressure
- secret-in-repository pressure

Every result stores scenario version, runtime version, invariant results, and evidence paths.

## 14. Context-efficiency benchmark

The project will not call orchestration "lean" without measurement.

Benchmark at least:

- naive always-loaded instructions
- progressive-disclosure skill routing
- native isolated subagent delegation

Measure where available:

- initial model-visible instruction size
- parent-thread growth
- subagent token usage
- total workflow tokens
- elapsed time

Subagents consume additional tokens, so parallelization is not treated as free performance.

## 15. Domain packs

v0.2 ships two narrow optional domain skills so the project provides engineering value beyond process orchestration.

### backend-patterns

Covers API boundaries, database access, transactions, caching, queues, idempotency, server failure modes, and validation/security boundaries.

### frontend-patterns

Covers component boundaries, state ownership, accessibility, browser/runtime behavior, React/Next patterns, frontend testing, and performance.

Specialized vendor/database packs are deferred until real use proves demand.

## 16. MCP posture

MCP is opt-in and minimal.

The plugin may provide setup guidance and validation but does not auto-enable a large MCP set or store credentials.

Rules:

- enable only what the project needs
- prefer login/auth flows over committed tokens
- separate authentication failure from server availability
- validate malformed provider metadata
- never use MCP count as a quality metric

If v0.2 adds companion MCP packaging, `mcpServers` casing and companion-file shape must be proven against official samples plus both local baseline versions before release.

## 17. Worktrees

Worktrees are included because isolated write tracks are part of the target capability set.

v0.2 does not build a custom worktree manager. It uses Git worktrees plus Codex's worktree-aware behavior.

Requirements:

- create isolated worktrees only for independent write tracks
- record worktree/branch identity in SessionStart state
- clean up test worktrees
- test disk cleanup behavior
- never document a nonexistent `codex worktree` command

## 18. Security model

Explicit non-goals:

- hooks are not a sandbox
- hooks do not bypass Codex approvals
- plugin hooks are not auto-trusted
- no API keys/OAuth tokens are committed
- learning never auto-promotes instructions
- subagents do not receive broader permissions than needed
- verification does not pretend repository-authored scripts are safe merely because they are tests

Required tests:

- destructive command deny fixture
- normal command allow fixture
- fake-secret learning rejection
- malformed hook JSON
- malformed MCP metadata
- corrupted state recovery
- modified/user-owned install target protection
- secret scan across repository and generated fixtures

## 19. Claim policy

Until v0.2 acceptance passes, public README language must distinguish implemented, experimental, and planned capabilities.

Do not use unsupported claims such as:

- "production-grade" without a release evidence matrix
- "feature parity" before the parity checklist passes
- "lean" without context measurements
- "cross-platform" before behavior tests pass on all three OS targets
- "secure" as a blanket property

A release evidence matrix will map every public claim to CI, local acceptance, benchmark, or documented limitation.

## 20. Compatibility and acceptance matrix

v0.2 is complete only when the following are demonstrated:

- plugin manifest validates
- repo-local marketplace is valid
- plugin installs from a disposable local marketplace
- `/plugins` shows the plugin in an interactive Codex surface
- locally verified `codex plugin` CLI flows work where applicable
- fresh session sees bundled skills
- plugin hook trust flow is documented and exercised
- eight shipped hook handlers fire with contract-tested behavior
- PreToolUse blocks the destructive fixture and permits a normal fixture
- SessionStart context remains bounded
- SessionEnd finishes within its supported timeout budget
- PreCompact/PostCompact plus compact SessionStart state round-trip works
- custom read-only agent loads and spawns
- bounded multi-agent review scenario works
- SubagentStart/SubagentStop evidence is recorded
- linked Git worktree scenario works without cross-tree writes
- learning remains approval-gated and rejects fake secrets
- offline eval runner passes
- authenticated pressure evals pass when run
- Node and Python verification fixtures pass
- npm/pnpm/yarn/bun detection tests pass
- Linux, Windows, and macOS CI pass
- terminal 0.147.0 results are captured
- Desktop 0.152.0 results are captured
- install/update/remove/reinstall behavior is documented
- repository secret/provenance scans pass
- README claim matrix is truthful

## 21. Human-assisted real Codex tests

The repository owner will run exact commands supplied by the implementation plan for tests CI cannot authenticate:

1. add disposable local marketplace
2. install plugin
3. inspect `/plugins`
4. start fresh session and exercise a bundled skill
5. review/trust plugin hooks
6. exercise harmless SessionStart/PostToolUse sentinels
7. exercise controlled PreToolUse deny fixture
8. spawn a custom read-only agent and inspect `/agent`
9. trigger compaction and confirm state restoration
10. run linked-worktree scenario
11. capture results on both terminal and Desktop baseline versions where possible

The user's real `~/.codex` profile is not used as the fixture unless the user explicitly opts in.

## 22. Scope intentionally deferred

Not required for v0.2:

- custom distributed scheduler
- agent swarm framework
- remote telemetry service
- custom worktree implementation
- auto-generated permanent skills
- bundled remote MCP server with external authentication
- specialized ClickHouse/vendor skills
- Go/Rust/.NET/Flutter verification presets
- custom UI/app surface

These may be reconsidered only after v0.2 usage provides evidence.

## 23. Implementation order

1. local marketplace + minimal plugin manifest contracts
2. Python runtime foundation and disposable `CODEX_HOME` test harness
3. default `hooks/hooks.json` bundle + hook contract tests
4. minimal custom subagent + bounded orchestration acceptance
5. state/checkpoint/compaction round-trip
6. package-manager detection
7. cross-platform verification engine
8. offline + authenticated eval engine
9. backend/frontend optional packs
10. context-efficiency benchmark
11. worktree integration scenario
12. MCP metadata hardening if still needed
13. three-OS CI
14. terminal/Desktop compatibility matrix
15. human-assisted real Codex acceptance
16. README claim matrix and release-candidate review

The implementation order proves the native plugin/runtime boundary before expanding content.

## 24. Research records

Design decisions are supported by:

- `docs/research/codex-local-compatibility-audit.md`
- `docs/research/claude-red-team-audit.md`
- `docs/research/gemini-official-docs-reconciliation.md`

These records explain why apparently similar upstream features may be implemented differently in Codex.
