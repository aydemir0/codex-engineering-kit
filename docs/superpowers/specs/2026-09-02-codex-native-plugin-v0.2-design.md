# Codex Engineering Kit v0.2 — Codex-Native Plugin Architecture

Status: design approved in chat; implementation requires final spec review.

## 1. Goal

Turn Codex Engineering Kit from a PowerShell-first toolkit into a first-class Codex plugin that captures the useful engineering capabilities demonstrated by mature Claude Code setups while being rebuilt around native Codex primitives rather than emulating Claude behavior.

The target is feature parity at the capability level, not file-for-file parity.

The public claim after completion should be defensible:

> Codex Engineering Kit is a Codex-native engineering workflow plugin built around skills, custom subagents, lifecycle hooks, verification, evals, review-gated learning, MCP integration, and cross-platform automation.

## 2. Design principles

1. Codex-native first. Use official Codex hooks, custom subagents, skills, plugins, MCP, worktrees, and non-interactive automation where supported.
2. Evidence before claims. Verification, performance, security, and architecture recommendations require repository or runtime evidence.
3. Correctness before speed. Parallelism is bounded and only introduced where it improves a measured or clearly decomposable workflow.
4. Progressive disclosure. Keep the active skill catalog lean; load domain-specific knowledge only when selected.
5. Secure by default. No secrets in repository files, no silent destructive actions, no automatic promotion of learned behavior.
6. Cross-platform runtime. Windows, macOS, and Linux are first-class targets.
7. Test the integration boundary. A plugin is not complete because its files validate; it must install and run in real Codex sessions.
8. Honest provenance. Upstream inspiration is attributed, but this project remains an independent Codex-native implementation.

## 3. Capability map

### Already present in v0.1

- core skills: orchestrator, verification-loop, eval-harness, continuous-learning, software-architecture, concurrency-performance
- role contracts for architect, planner, reviewer, security, build, E2E, TDD, refactor, and docs
- engineering/security/testing/performance/Git rules
- dev/review/research contexts
- workflow documents
- PowerShell install/update/uninstall lifecycle
- verification runner
- review-gated learning candidate extraction
- secret-safe MCP templates
- Linux and Windows CI

### Required for v0.2 parity

- `.codex-plugin/plugin.json`
- local marketplace installation and `/plugins` discovery
- native Codex hooks
- native custom subagents under `.codex/agents/*.toml`
- lifecycle-based memory/checkpoint persistence
- pre/post-compaction state preservation
- deterministic PreToolUse policy hooks
- PostToolUse evidence capture
- native subagent lifecycle observation
- package manager detection
- cross-platform runtime implementation
- executable eval harness
- worktree/parallel-agent workflow
- optional backend/frontend engineering packs
- multi-language verification presets
- fresh-install, upgrade, disable, uninstall, and recovery tests
- submission/readiness documentation

## 4. Proposed repository architecture

```text
codex-engineering-kit/
├── .codex-plugin/
│   └── plugin.json
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
├── evals/
│   ├── capability/
│   ├── regression/
│   ├── pressure/
│   └── fixtures/
├── verification/
│   ├── presets/
│   └── runners/
├── workflows/
├── rules/
├── mcp/
├── scripts/
├── tests/
└── docs/
```

## 5. Native plugin packaging

The plugin manifest is the primary installation surface. Legacy PowerShell installation remains only as a compatibility/fallback path.

Minimum manifest responsibilities:

- stable plugin name and semantic version
- plugin description
- skills directory
- hook bundle
- optional MCP metadata only where safe and useful

No credential values may be stored in plugin metadata.

A local marketplace will be used for development. Success requires the plugin to appear in Codex CLI `/plugins`, install cleanly, start a fresh session, and expose its bundled skills.

## 6. Native subagent model

The current markdown role references become executable Codex subagents.

Agents are separated by permissions and responsibility:

### Read-only evidence agents

- explorer: maps execution paths and repository ownership
- architect: evaluates boundaries and alternatives
- reviewer: finds correctness/regression/test risks
- security-reviewer: threat-focused analysis
- docs-researcher: verifies version-specific APIs/documentation

### Controlled write agents

- build-resolver: narrowly fixes reproducible build failures
- e2e-runner: may create/update test artifacts where requested
- refactor-cleaner: removes proven dead code with verification

The primary Codex session remains the coordinator. Read-only agents should be preferred before write-capable agents.

Concurrency is bounded. The orchestrator must not spawn unlimited agents or duplicate independent research unnecessarily.

## 7. Hook architecture

Hooks extend Codex; they do not replace sandboxing, approvals, or security boundaries.

### SessionStart

Purpose:

- identify repository/worktree/branch
- load compact workspace checkpoint
- expose unresolved verification or learning state as bounded developer context

Must not load entire transcripts or large historical logs.

### SessionEnd

Purpose:

- save a cheap deterministic snapshot
- mark learning/eval candidates for later processing

It must not perform expensive model-driven learning synchronously.

### PreToolUse

Purpose:

- block a small set of clearly destructive operations
- attach context for generated/vendor/managed files
- flag unsafe secret-handling patterns

This is a guardrail, not a complete enforcement boundary.

### PostToolUse

Purpose:

- record bounded evidence for relevant shell/test/build actions
- update verification state without declaring success solely from tool invocation

### PreCompact

Purpose:

- persist critical state before compaction
- store active plan/checkpoint identifiers and unresolved failures

### PostCompact / compact SessionStart

Purpose:

- restore only critical state needed for continuation
- avoid replaying historical conversation content

### SubagentStart/SubagentStop

Purpose:

- record agent role, scope, outcome, and evidence location
- detect duplicate work or failed delegation

## 8. State and memory design

Runtime state must live outside committed source files by default.

Suggested workspace data:

```text
.codex-kit/
├── state.json
├── checkpoints/
├── evidence/
├── learning-candidates/
└── eval-results/
```

`.codex-kit/` is gitignored by default.

State records must be versioned and bounded. Sensitive text is filtered before persistence. Full chat transcripts are not treated as a stable storage contract.

## 9. Continuous learning

Learning remains review-gated.

Flow:

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

No hook can directly create or activate a permanent skill.

Candidates must contain provenance: which task, evidence, failure, and successful correction produced the pattern.

## 10. Verification system

Verification moves from one PowerShell runner to a cross-platform engine with project-specific presets.

Initial presets:

- Node/TypeScript
- Python
- generic repository

Detection sources:

- package manifests and lockfiles
- project config
- known test/build/typecheck/lint commands

Every step records command, exit code, duration, and status: passed, failed, skipped, or unavailable.

Skipped is never reported as passed.

Later presets may add Flutter/Dart, Go, Rust, and .NET.

## 11. Package manager detection

For Node projects the resolution order is:

1. explicit Codex Engineering Kit project setting
2. `packageManager` in `package.json`
3. lockfile detection
4. globally available managers
5. npm fallback only when valid

Supported initially: npm, pnpm, yarn, bun.

Conflicting lockfiles produce a warning rather than an arbitrary silent choice.

## 12. Executable eval harness

The current eval skill becomes an executable system.

Eval classes:

- capability: can the toolkit perform a target workflow?
- regression: does an existing behavior still hold?
- pressure: does the agent refuse unsafe or unsupported shortcuts under explicit pressure?

Each eval defines:

- fixture/workspace
- prompt/scenario
- expected invariants
- deterministic checks where possible
- optional model/human grader notes
- result artifact

Initial pressure evals include:

- unsupported performance claim pressure
- unbounded concurrency pressure
- destructive shell pressure
- skip-tests-and-ship pressure
- secret-in-repository pressure

## 13. Parallelism and worktrees

Parallel agents are used only for independent tasks.

Preferred workflow:

```text
root coordinator
├── explorer (read-only)
├── reviewer (read-only)
└── docs/security agent (read-only)
        ↓
coordinator synthesizes
        ↓
write agent or root implements
        ↓
verification
```

For independent implementation tracks, isolated Git worktrees are required. Two write agents must not edit the same working tree concurrently.

## 14. Domain packs

Backend and frontend knowledge are useful but must not inflate the always-visible skill surface.

They are optional skills/packs with narrow trigger descriptions.

Backend pack covers API boundaries, database access, transactions, caching, queues, idempotency, and server failure modes.

Frontend pack covers component boundaries, state ownership, accessibility, browser behavior, React/Next patterns, testing, and performance.

Specialized database/vendor packs are deferred until demonstrated by real use.

## 15. MCP design

MCP remains opt-in and minimal.

The plugin may provide setup metadata, guidance, and validation, but it must not auto-enable large MCP sets or store credentials.

Principles:

- enable only what the project needs
- prefer authentication/login flows over committed tokens
- validate missing auth separately from server availability
- avoid turning MCP count into a feature metric

## 16. Cross-platform strategy

Python 3 is the preferred cross-platform hook/runtime language because Codex hook commands need a stable executable surface across Windows/macOS/Linux and the runtime work is primarily filesystem/process/JSON logic.

PowerShell scripts remain for Windows-friendly compatibility and migration, but core plugin behavior must not depend on PowerShell.

CI matrix target:

- ubuntu-latest
- windows-latest
- macos-latest

## 17. Testing strategy

Test layers:

1. unit tests for runtime modules
2. hook input/output contract tests
3. policy/security tests
4. state persistence and corruption recovery tests
5. package-manager detection tests
6. eval-runner tests
7. plugin manifest/content validation
8. fresh install and upgrade tests where automation permits
9. real Codex CLI acceptance tests performed locally when CI cannot provide authenticated Codex

No feature is considered complete only because a markdown file exists.

## 18. Migration from v0.1

- preserve existing skill names where stable
- migrate role references into native agent TOML while keeping human-readable documentation
- keep current PowerShell installer until plugin install is proven
- replace wrapper-emulated lifecycle behavior with native hooks
- keep v0.1 verification behavior as a regression target while introducing the cross-platform runner
- do not break users who installed existing skills manually

## 19. Security model

Explicit non-goals:

- hooks are not a security sandbox
- the toolkit does not bypass Codex approvals
- the toolkit does not auto-trust plugin hooks
- the toolkit does not store API keys or OAuth tokens
- learning never auto-promotes permanent instructions
- subagents do not receive broader permissions than required by role

Dangerous-operation policy begins intentionally small and testable rather than trying to parse every possible shell command.

## 20. Provenance and differentiation

The repository will credit Everything Claude Code and other upstream inspirations in `THIRD_PARTY_NOTICES.md` where applicable.

Differentiators:

- native Codex plugin packaging
- native Codex hooks
- native custom subagents
- explicit permission separation
- evidence-linked continuous learning
- executable pressure evals
- cross-platform verification
- safe MCP posture
- bounded context and progressive disclosure

The project must not claim endorsement by OpenAI or Anthropic and must not claim that the upstream repository itself was a hackathon-winning submission.

## 21. Completion criteria for v0.2

v0.2 is complete only when all of the following are demonstrated:

- plugin manifest validates
- local marketplace entry installs
- plugin appears in Codex CLI `/plugins`
- a fresh Codex session sees bundled skills
- native hooks fire with contract-tested behavior
- destructive policy test is blocked without breaking normal commands
- custom subagents are discoverable and at least one read-only orchestration scenario works
- SessionStart/compaction state round-trip works
- continuous-learning candidate flow remains approval-gated
- capability/regression/pressure eval runner executes
- verification works on sample Node and Python fixtures
- npm/pnpm/yarn/bun detection tests pass
- Linux, Windows, and macOS CI pass
- fresh install, update, disable/uninstall behavior is documented and tested as far as the product permits
- secret scan and provenance checks pass
- real Windows Codex acceptance test passes
- README documents architecture and limitations honestly

## 22. Human-assisted acceptance tests

The following steps may require a real authenticated Codex CLI and therefore will be delegated to the repository owner when CI cannot exercise them:

1. install the local marketplace/plugin
2. confirm `/plugins` listing and enable state
3. start a new Codex session and confirm bundled skills
4. trigger a harmless SessionStart/PostToolUse hook flow
5. run a controlled PreToolUse deny fixture
6. invoke a custom read-only subagent
7. test compact/resume state restoration

The assistant must provide exact commands and expected output for each manual checkpoint.

## 23. Implementation order

1. plugin manifest + local marketplace contract
2. cross-platform runtime foundation
3. native hooks + tests
4. native subagents + orchestration contract
5. state/checkpoint/compaction persistence
6. package manager detection
7. executable verification engine
8. executable eval engine + pressure scenarios
9. optional backend/frontend packs
10. MCP/plugin integration hardening
11. three-OS CI
12. real Codex acceptance tests
13. documentation, release candidate, submission-readiness review

This order intentionally proves the native plugin/runtime boundary before expanding content packs.
