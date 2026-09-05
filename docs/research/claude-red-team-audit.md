# Claude Adversarial Review — Synthesis

Date: 2026-09-02
Status: research input for v0.2 design; not an implementation claim

## Scope caveat

The external reviewer explicitly stated that it reviewed both repositories primarily at the README/structure level and did not deeply inspect every skill, script, hook, or workflow implementation. Findings below are therefore treated as adversarial design input, not authoritative runtime evidence.

## Accepted findings

These findings are valid and should influence v0.2:

- v0.1 is process-heavy and still light on day-to-day domain knowledge.
- backend and frontend domain packs should be added as optional, narrowly triggered skills rather than always-visible context.
- package-manager detection should become a reusable runtime abstraction instead of verification-local logic.
- verification should move off PowerShell-only execution into a cross-platform runtime.
- executable eval fixtures are required; an eval skill alone is not enough.
- worktrees and bounded parallel-agent workflows deserve explicit architecture and tests.
- context/token-efficiency claims must be measured instead of asserted.
- verification executes project-authored commands and therefore must document that it is active execution, not passive inspection.
- local/generated runtime state and MCP metadata must be gitignored and secret-filtered by default.
- distribution integrity and update safety need a clearer story than local manifest hashing alone.
- one sample JavaScript project is insufficient; Node and Python fixtures are required for v0.2.
- public claims must track demonstrated capability, not planned capability.

## Already addressed by the v0.2 design

Several findings correctly describe v0.1 but are already explicit v0.2 work items:

- native plugin packaging
- native lifecycle hooks
- automatic session/checkpoint persistence
- compaction lifecycle handling
- native custom subagents
- cross-platform runtime
- package-manager detection
- executable eval harness
- worktree/parallel-agent workflow
- backend/frontend optional packs
- three-OS CI
- real Codex acceptance tests

These remain open until implemented and tested; being present in the design does not count as completion.

## Findings superseded by local Codex evidence

The external reviewer was intentionally uncertain about Codex-native primitives. The local compatibility audit resolved several of those questions:

- Codex plugin support exists.
- local plugin marketplaces exist.
- `.codex-plugin/plugin.json` is the native plugin manifest location.
- hooks are recognized by the installed engine.
- `.codex/agents/*.toml` custom-agent discovery is supported at parser/discovery level.
- `codex exec` exists.
- worktree-aware behavior exists, although no standalone `codex worktree` command exists.

Therefore v0.2 should replace the wrapper-emulation architecture rather than preserve it as the primary lifecycle mechanism.

## Findings accepted with modification

### Domain skills

Do not mirror upstream's entire domain catalog. Add backend and frontend packs first, measure actual usage, and keep trigger descriptions narrow. Language/vendor packs remain deferred until demand is demonstrated.

### Coding standards and TDD/security skills

Do not automatically duplicate concepts already represented by rules, workflows, and security tooling. Add a dedicated skill only when it provides a distinct trigger and reusable workflow that cannot be represented cleanly elsewhere.

### Context efficiency

Do not use file count as a proxy for context savings. v0.2 requires an explicit measurement comparing at least:

1. naive always-load baseline
2. progressive-disclosure skill routing
3. native subagent delegation with isolated context

### Public positioning

Until the v0.2 completion criteria pass, README language should distinguish implemented v0.1 capability from planned v0.2 capability. "Production-grade" should only be retained where the repository can demonstrate a concrete tested subsystem, not used as an umbrella claim for unfinished integrations.

## Findings rejected or deferred

### "Do not add plugin packaging, worktrees, or parallelization until v0.3"

Rejected for this project's stated goal. The objective is a credible Codex-native counterpart at the capability level, and local Codex evidence shows these are real platform primitives/integration paths. However, implementation must remain minimal and test-first rather than broad for its own sake.

### Replace Python with Node solely because upstream did

Deferred. Cross-platform runtime language must be selected by dependency availability, startup cost, packaging, hook ergonomics, Windows/macOS/Linux support, and Codex acceptance-test evidence. Upstream's Node choice is useful evidence, not a binding architecture decision.

### Role references are inherently wrong

Accepted only as a v0.1 limitation. For v0.2, native subagents become the execution primitive. Human-readable role references may remain documentation or fallback material, but must not be marketed as equivalent to isolated subagents.

## Security actions for v0.2

Required tests and documentation:

- fake-secret rejection in learning candidates
- malformed/malicious MCP metadata fixtures
- runtime-state gitignore enforcement
- verification warning for project-authored command execution
- destructive PreToolUse policy fixtures
- supply-chain/update model documentation
- plugin/version pinning guidance where supported

## Additional acceptance criteria added from the review

v0.2 should not be considered complete until it also demonstrates:

- at least one backend-domain workflow fixture
- at least one frontend-domain workflow fixture
- token/context measurement for the orchestration strategy
- adversarial secret-rejection test
- malformed MCP metadata test
- explicit documentation that verification executes repository-defined commands
- README claim audit against the implemented feature matrix

## Decision

The adversarial review is useful and materially changes quality gates, but it does not invalidate the v0.2 direction. The correct response is not to shrink back to v0.1; it is to implement the already-approved Codex-native architecture with stricter runtime evidence, narrower claims, measurable context efficiency, and stronger adversarial tests.
