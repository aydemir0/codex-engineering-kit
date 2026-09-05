# Plan E Manual Worktree Acceptance Evidence

Date: 2026-09-04

## Scope

This evidence binds the Plan E implementation exit gate to feature-branch head `d562708975d66a6154342e58c75165f228ef088e` and GitHub Actions CI run #147 (`33918808854`). The Plan E delta is measured from the explicit Plan D closure commit `3ec1cc739d904c67fab1d1c71d43d799dec4446f`.

This document records bounded acceptance facts only. It does not establish release compatibility, repeated benchmark reliability, or a measured `lean` result.

## Manual Git worktree acceptance

The Ubuntu `plan-e-contracts` job ran the worktree acceptance suite on Git `2.55.0`. The suite completed three tests successfully:

- normal disposable manual-Git lifecycle: PASS;
- dirty source refusal before integration: PASS;
- unowned/foreign worktree cleanup refusal: PASS.

The passing normal-lifecycle contract requires all of the following values from `run_manual_worktree_acceptance`:

- `status = PASS`
- `gitVersion = git version 2.55.0`
- `detachedCreation = true`
- `uniqueBranches = true`
- `isolatedWrites = true`
- `cleanBeforeIntegration = true`
- `conflictStopped = true`
- `cleanupPassed = true`
- `remainingFixtureWorktrees = 0`
- `blockers = []`

The helper creates its own temporary Git repository, creates two detached worktrees before assigning unique fixture branches, verifies isolated writes, refuses integration from a dirty source, stops on the deliberate merge conflict without editing the conflicted file, aborts that merge, removes only paths recorded as owned by the current fixture run, verifies zero remaining fixture worktrees, and prunes only after live fixture entries are gone.

No temporary fixture path is persisted or published in the acceptance record.

## Domain-skill contracts

The same fresh CI run passed `tests.test_domain_skills` on Ubuntu, Windows, and macOS. The repository contains the optional `backend-patterns` and `frontend-patterns` skills with narrow entry conditions and repository-evidence requirements. Their contracts prohibit unsupported performance claims and framework boilerplate being treated as universal architecture.

This proves the shipped skill contracts and their deterministic validation only; it is not a blanket backend/frontend expertise or coverage claim.

## Benchmark implementation boundary

Plan E fixes three configurations:

- A: naive always-loaded engineering instructions;
- B: progressive-disclosure skill routing;
- C: native isolated subagent delegation.

The five benchmark cases are pinned to fixture commit `1dbf382b6e838ca351c6fb8818a64aa793176198`. A complete campaign definition is 5 tasks × 3 configurations × 3 repeats = 45 real runs with one model, reasoning setting, and Codex runtime version per campaign.

The report engine validates completeness, preserves token evidence sources (`measured`, `exported`, `estimated`, `unavailable`) separately, and reports median plus range without statistical-significance or pass@k-style claims.

The committed synthetic result fixtures are reporting self-tests only. No real authenticated 45-run Plan E context-efficiency campaign has been executed as part of this closure, so no measured `lean` or context-efficiency result is claimed.

## Fresh deterministic CI gate

CI run #147 completed successfully on head `d562708975d66a6154342e58c75165f228ef088e` with all required jobs green:

- `plan-e-contracts`: Ubuntu, Windows, macOS;
- `plan-d-contracts`: Ubuntu, Windows, macOS;
- `content-contracts`;
- `powershell-contracts`, including the Windows installer lifecycle.

The Plan E matrix also passed the worktree acceptance suite, domain-skill suite, benchmark contract suite, repository content validator, and offline benchmark protocol validation.

## Delta audit

The audited Plan E range is `3ec1cc739d904c67fab1d1c71d43d799dec4446f..d562708975d66a6154342e58c75165f228ef088e`: 12 commits and 36 changed files.

The audit found no committed secret-like value, machine-local user path, active Claude-specific path, shipped TODO/TBD placeholder, unsupported blanket backend/frontend coverage claim, or wording that presents synthetic benchmark data as measured evidence. Secret/path/TODO strings present in tests are detection patterns or negative assertions, not credentials, active machine paths, or placeholders.

## Open limitations

Plan E closure does not close or weaken these separate open items:

- RISK-001: explicit manifest `hooks` override compatibility;
- RISK-002: runtime skew/compatibility;
- Codex CLI 0.147.0 SessionEnd timeout discrepancy;
- Plan F release/compatibility/submission evidence;
- real authenticated 45-run context-efficiency measurement.
