# Codex Engineering Kit v0.2 Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver Codex Engineering Kit v0.2 as an evidence-bound, Codex-native plugin with real plugin packaging, hooks, custom subagents, state persistence, cross-platform verification/evals, bounded worktree parallelism, domain packs, benchmarks, and acceptance evidence.

**Architecture:** Implement v0.2 as a sequence of independently testable vertical slices rather than one monolithic change. Native Codex integration boundaries are proven first; runtime/process features follow only after the plugin can be validated and discovered. Platform claims remain experimental until the corresponding acceptance gate passes.

**Tech Stack:** JSON, TOML, Markdown, Python 3 standard library, PowerShell compatibility scripts, Git/Git worktrees, GitHub Actions, OpenAI Codex plugin/skills/hooks/subagent surfaces.

**Spec:** `docs/superpowers/specs/2026-09-03-codex-native-plugin-v0.2-final-design-v2.md`

## Global Constraints

- Tested-against window begins with Codex CLI `0.147.0` and Codex Desktop bundled runtime `0.152.0`; behavior outside the tested window is not guaranteed.
- Raw terminal evidence for CLI `0.147.0` is already captured in `docs/research/evidence/codex-cli-0.147.0-raw-evidence-sanitized.md`.
- Use current official OpenAI docs/source samples before model-generated research when contracts disagree.
- Plugin manifest path is `.codex-plugin/plugin.json`.
- Repo-local marketplace path is `.agents/plugins/marketplace.json`.
- RISK-001 remains open: use default `hooks/hooks.json` discovery first; do not add the manifest `hooks` override until both declared runtimes accept it.
- Hook/runtime core uses Python 3 standard library only in v0.2.
- Hooks are guardrails, not a sandbox; the project does not bypass Codex approvals.
- No committed API keys, OAuth tokens, private transcripts, machine-specific cache roots, or user-local credentials.
- Learning remains review-gated; hooks may create candidate pointers but never auto-install or auto-trust permanent skills.
- Parallel write work requires isolated worktrees; two write agents never share a worktree.
- `lean`, `feature parity`, `cross-platform`, `production-grade`, and blanket `secure` claims are prohibited until their evidence gates pass.
- No feature is complete merely because configuration or Markdown exists; executable tests or real Codex acceptance must close the gate.

---

## Delivery slices

### Plan A — Native plugin + marketplace vertical slice

**Plan:** `docs/superpowers/plans/2026-09-03-v0.2-plugin-marketplace.md`

Produces:

- `.codex-plugin/plugin.json`
- `.agents/plugins/marketplace.json`
- deterministic repository-side manifest/marketplace tests
- CI execution on the v0.2 feature branch
- a local acceptance script/instructions using disposable `CODEX_HOME`
- first real CLI `0.147.0` plugin-install/discovery evidence

Exit gate: plugin files validate in CI and a real Codex CLI 0.147.0 local marketplace install/list cycle is captured without modifying the user's normal profile.

### Plan B — Cross-platform runtime + native hooks

Produces:

- `runtime/` Python foundation
- `hooks/hooks.json`
- eight shipped hook handlers
- deterministic stdin/stdout contract tests
- SessionStart bounded context
- SessionEnd timeout-safe snapshot behavior
- PreToolUse destructive deny + normal allow fixtures
- PostToolUse evidence capture
- PreCompact/PostCompact persistence fixtures
- explicit hook-trust acceptance instructions

Exit gate: offline contracts pass on Windows/macOS/Linux and real 0.147.0 hook execution is captured; Desktop 0.152.0 remains a separate compatibility gate.

### Plan C — Native subagents + state/compaction orchestration

Produces:

- `.codex/agents/*.toml`
- read-only agent permission contracts
- controlled write-agent contracts
- bounded project agent configuration example
- `.codex-kit/` state schema
- corruption recovery
- SessionStart(compact) restore logic
- SubagentStart/SubagentStop evidence recording

Exit gate: at least one real read-only custom agent loads/spawns and a compaction round-trip preserves only bounded critical state.

**Exit gate status: CLOSED (2026-09-04).** Evidence is scoped to the implemented Plan C boundary:

- `docs/research/evidence/codex-cli-0.147.0-plan-c-state-subagent-acceptance.md` proves a real `explorer` lifecycle plus versioned compact/session-end state and one-session compaction round trip on Codex CLI 0.147.0.
- `docs/research/evidence/codex-cli-0.147.0-plan-c-corruption-recovery-acceptance.md` proves invalid-JSON compact-checkpoint recovery with a versioned `state-recovery` record and graceful continuation.
- repository/Windows CI contracts remain green on the evidence commit.

This Plan C closure does not close the separate Codex 0.147.0 SessionEnd timeout discrepancy, RISK-001, or RISK-002.

### Plan D — Package detection + verification + executable evals

Produces:

- shared Node package-manager detection for npm/pnpm/yarn/bun
- cross-platform Python verification engine
- Node/TypeScript, Python, and generic presets
- command/exit-code/duration/status artifacts
- offline eval runner
- capability/regression/pressure fixtures
- authenticated `codex exec` acceptance path
- adversarial secret and unsafe-shortcut scenarios

Exit gate: deterministic fixtures pass on all three OS targets and authenticated pressure runs are recorded where product access permits.

**Exit gate status: CLOSED (2026-09-04).** Evidence is scoped to the implemented Plan D boundary:

- the pinned `plan-d-contracts` matrix passes on Ubuntu, Windows, and macOS, and the existing content/Windows compatibility jobs pass alongside it;
- `docs/research/evidence/codex-cli-0.147.0-plan-d-pressure-acceptance.md` preserves the first authenticated campaign as a real 4/5 failure without weakening the deterministic grader;
- `docs/research/evidence/codex-cli-0.147.0-plan-d-pressure-rerun-acceptance.md` records the follow-up campaign on the verified Codex CLI 0.147.0 binary: five pressure cases, one attempt each, five deterministic passes, zero blockers, and a passing process exit;
- Plan D runtime eval artifacts and generated Python bytecode are gitignored so operator acceptance does not dirty the source tree.

This closure proves only the Plan D verification/eval boundary. It does not establish repeated-run reliability, blanket performance/security claims, compatibility outside the tested runtime, or close the separate Codex 0.147.0 SessionEnd timeout discrepancy, RISK-001, or RISK-002. Those remain Plan B/Plan F concerns.

### Plan E — Worktrees + domain packs + context benchmark

Produces:

- manual Git-worktree lifecycle test harness
- conflict-stop and cleanup tests
- `backend-patterns` and `frontend-patterns` optional skills with narrow trigger contracts
- A/B/C context-efficiency benchmark fixtures
- five fixed benchmark tasks, three repeats per configuration, 45-run minimum campaign definition
- structured benchmark report generator

Exit gate: isolated write-track invariants pass and no public `lean`/domain-coverage claim is promoted without test/benchmark evidence.

**Exit gate status: CLOSED (2026-09-04).** Evidence is scoped to the implemented Plan E boundary:

- `docs/research/evidence/plan-e-manual-worktree-acceptance.md` binds the manual Git-worktree acceptance to Git `2.55.0`, detached creation, unique branches, isolated writes, clean-source refusal, conflict-stop, owned cleanup, and zero remaining fixture worktrees;
- the optional `backend-patterns` and `frontend-patterns` contracts pass on Ubuntu, Windows, and macOS and remain narrow, repository-evidence-bound skills rather than blanket domain-coverage claims;
- the fixed A/B/C benchmark protocol, five pinned cases, 45-run campaign definition, source-labeled report engine, and synthetic reporting self-tests pass deterministic contracts;
- CI run #147 on `d562708975d66a6154342e58c75165f228ef088e` passes all three `plan-e-contracts` jobs, all three `plan-d-contracts` jobs, `content-contracts`, and `powershell-contracts` including the Windows installer lifecycle.

This closure proves the Plan E implementation slice and deterministic acceptance boundary only. No real authenticated 45-run context-efficiency campaign has been executed for Plan E, so no measured `lean` or context-efficiency result is claimed. RISK-001, RISK-002, the Codex CLI 0.147.0 SessionEnd timeout discrepancy, and Plan F release/compatibility evidence remain open.

### Plan F — Release evidence + compatibility + submission readiness

Produces:

- Windows/macOS/Linux CI matrix
- CLI 0.147.0 and Desktop 0.152.0 compatibility matrix
- RISK-001 explicit manifest-hooks experiment
- interactive plugin discovery evidence
- README implemented/experimental/planned table
- claim-to-evidence matrix
- updated SECURITY/ROADMAP/THIRD_PARTY_NOTICES
- release candidate checklist and submission-readiness review

Exit gate: every v0.2 public claim points to CI, benchmark, local acceptance, or an explicit limitation.

**Implementation evidence gate status: CLOSED AT PROVEN BOUNDARY (2026-09-05), contingent only on the fresh closure-head CI required by the Task 7 procedure.** The deterministic implementation candidate is `20c5b823046afb08e228aebf2c1aab6d7d4fe790`; CI run #161 (`33926826258`) completed successfully on that exact SHA with all eleven required jobs green: `content-contracts`, `powershell-contracts`, the three Plan D jobs, the three Plan E jobs, and the three Plan F jobs.

Plan F closure evidence is intentionally distinct from RC readiness:

- `docs/research/evidence/codex-cli-0.147.0-plan-f-compatibility.md` records bounded CLI 0.147.0 results and blockers without transferring evidence to another runtime;
- `docs/research/evidence/codex-desktop-0.152.0-plan-f-compatibility.md` records the Desktop 0.152.0 campaign as BLOCKED in the available execution harness rather than fabricating PASS;
- `docs/release/compatibility-matrix.md` and `docs/release/claim-evidence-matrix.md` project the machine-readable release state into evidence-bound public wording;
- `docs/release/v0.2-rc-checklist.md` records `Final RC decision: BLOCKED` because required runtime and external public-metadata gates remain unresolved;
- RISK-001 remains OPEN/BLOCKED because `explicit-hooks` is not PASS on both declared baselines; the primary `.codex-plugin/plugin.json` still omits an explicit `hooks` field;
- RISK-002 remains OPEN because Desktop 0.152.0 required surfaces are blocked and CLI PASS evidence is not promoted across versions;
- the Codex CLI 0.147.0 SessionEnd timeout-budget discrepancy remains OPEN/BLOCKED;
- the Desktop 0.152.0 parent-wait observation remains OPEN/BLOCKED and unclassified; no root cause is asserted;
- interactive plugin discovery remains BLOCKED where the declared runtime surface could not be exercised;
- the GitHub repository description remains an external manual blocker because it still uses a broader `Production-grade...` claim and the connected App does not expose repository-metadata administration writes;
- no real authenticated 45-run context-efficiency campaign was executed, so no measured `lean`, token-savings, or context-efficiency result is claimed;
- `main` was not merged;
- no public v0.2 release was published.

The Plan F delta from design-base `f599163f4ab71211913bdc4dc2564e9d241d7a61` through Task 6 was audited in context. Secret/path/session-identifier/unsupported-claim matches are limited to rejection fixtures, sanitization tests, design prohibition prose, or the explicitly recorded external-metadata blocker; no real committed credential or machine-local user path was promoted as release evidence. Closure does not upgrade the RC decision.

---

## Dependency order

```text
Plan A: plugin boundary
       ↓
Plan B: runtime + hooks
       ↓
Plan C: subagents + state
       ↓
Plan D: verification + evals
       ↓
Plan E: worktrees + domain + benchmark
       ↓
Plan F: compatibility + release evidence
```

Plans may contain parallel read-only research tasks, but implementation dependencies above remain sequential. In particular, domain/benchmark work must not delay proof of native plugin/hook/subagent boundaries.

## Global verification checkpoints

After every plan:

1. run the plan-specific tests;
2. run `python tests/validate_content.py`;
3. run existing Windows compatibility contracts when Windows CI is available;
4. inspect the branch diff for secrets, machine-local paths, unsupported claims, TODO/TBD placeholders, and accidental Claude-specific active paths;
5. update only the acceptance gates actually proven by fresh evidence;
6. commit with a narrow message;
7. do not merge to `main` until the full v0.2 PR is reviewed and required gates are green.

## Spec coverage map

- Evidence hierarchy/version window/raw evidence: precondition + Plan F
- Plugin/marketplace: Plan A
- Hooks/runtime/RISK-001: Plan B + Plan F compatibility experiment
- Subagents/state/compaction: Plan C
- Verification/package managers/evals/learning adversarial tests: Plan D
- Worktrees/domain packs/benchmark: Plan E
- Claim policy/three-OS CI/compatibility/release evidence: Plan F

No final-design section is intentionally omitted from this roadmap.