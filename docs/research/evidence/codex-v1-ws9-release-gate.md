# CEK v1 WS9 Final Release Gate Evidence

Date: 2026-09-13

Branch: `feat/v1-core-workflow`

Content candidate: `0093686627bd56976106deb1c5ad7093dae85dcf`

Runtime: Codex CLI 0.153.0

Host family: Windows

Result: `NOT_RELEASE_READY`

## Candidate and ancestry

The tracked worktree was clean before verification. `.serena/` was the sole
untracked path; it was inherited from the preceding workstreams and was not
read, staged, modified, or removed by WS9. Generated `.codex-kit/` hook state
remained ignored/local and was not promoted into release evidence.

All workstream boundaries are ancestors of the candidate:

| Workstream | Closure boundary |
| --- | --- |
| WS1 | `83823570cbfd8aa9d93dd9b0943c6a97adb38281` |
| WS2 | `7bd14fbeb77b3f56f4b97f9293a32de414ea38a5` |
| WS3 | `e449cc754088efddc070f54f97887d7f834b2171` |
| WS4 | `eea6f836ca995e23787cc3fd0309fb22de3792de` |
| WS5 | `78206e1a67800f21f059c7c699727fc3d40df9cf` |
| WS6 | `29bee4282ea21785d618dc477e984a3f44afc8d7` |
| WS7 | `5ff008a6aba7c143c2c1d48f96b380e469d7a147` |
| WS8 | `0093686627bd56976106deb1c5ad7093dae85dcf` |

The WS8 SHA supplied at handoff was not a Git object. Git independently
resolved the candidate above as the `evidence: close WS8 presentation` commit
with parent `bb54d45126b243e92f5a8c2913f2947b6d9f3929`.

## Fresh deterministic gates

| Gate | Fresh result on the candidate |
| --- | --- |
| Claims, runtime, architecture, presentation, plugin contracts | PASS — 56 tests |
| Workflow, fixture, agents, hooks, security, state, asset stocktake | PASS — 65 tests |
| Benchmark and authenticated-runner contracts | PASS — 34 tests |
| Clean-install lifecycle and documentation contracts | PASS — 15 tests |
| Full Python discovery | PASS — 253 tests |
| Offline deterministic eval campaign | PASS — 7/7 attempts, zero blockers |
| PowerShell install | PASS |
| PowerShell verification | PASS |
| PowerShell learning | PASS |
| PowerShell MCP | PASS |
| Repository content validator | PASS |
| Release-data validator | PASS — 13 claims, 13 compatibility surfaces |
| Benchmark protocol validator | PASS — 45 planned attempts |
| Python syntax compilation | PASS; disposable bytecode output removed |
| Public evidence secret/private-path scan | PASS — zero violations |
| Tracked authentication/local-runtime/raw evidence check | PASS — zero files |
| `git diff --check` | PASS |

Expected negative-fixture diagnostics from the full suite were retained as test
output and did not change the successful process result.

## Representative and representative workflow

The WS3 fixture, workflow validator, reviewer definition, and evidence document
are unchanged from the WS3 closure boundary. Fresh contracts confirmed the
ordered classify, plan, RED, implement, GREEN, review, and verify stages; the
fixture still begins in the expected deterministic RED state.

The retained authenticated record remains the reviewer runtime evidence: one
matching project-local reviewer `SubagentStart`/`SubagentStop` identity pair
with reviewer role/type. Parent prose is not accepted as lifecycle evidence.
No new authenticated reviewer run was required because no fresh evidence
contradicted the closed runtime contract.

## Security and asset stocktake

Fresh deterministic checks passed for prompt/instruction injection boundaries,
shell/tool guidance, destructive writes, secrets, state leakage, MCP/app
permissions, provenance, ownership-aware install/update/delete behavior,
learning promotion, metadata URLs, path handling, and immutable CI action
references.

The inventory remains exactly eight plugin-native skills, eight project-local
native agent definitions, and nine parent-context role contracts. Reviewer and
explorer retain direct CLI 0.153.0 lifecycle evidence; the other six agents are
contract-only. The PowerShell installer owns six core skills, while the two
domain packs remain plugin-only.

The security result does not remove documented TOCTOU link-change risk,
pattern-recognition limits, user-privilege command execution, or external
host/provider trust boundaries. Hooks are not a sandbox.

## Benchmark integrity

The normalized SHA-256 of `benchmarks/results/ws6-cli01530-v3.json` is:

`33761f665e5402d752e641cacbbfe1d5299835a3bd452a037acc7e9d6f5b3382`

The dataset and benchmark core are unchanged from WS6 and validate as exactly
45 counted runs: A 15/15 PASS, B 15/15 PASS, C 4/15 PASS, and 34 PASS / 11
retained FAIL. The failures remain nine `missing-subagent-lifecycle` and two
`quality-contract`. No failed counted attempt was retried or replaced.

No efficiency, token/context, latency, isolated-subagent, quality,
statistical-significance, or benchmark-leadership claim is made. The CLI 0.153
unauthorized connector startup warning remains a limitation, not proof of
connector isolation.

## Clean-install acceptance

The fresh disposable campaign bound its result to the exact content candidate
and passed clean install, verification, reviewer provisioning, reviewer
conflict refusal, prior-version update, post-update verification, uninstall,
verify-clean, byte-preserved sentinels, and reinstall. The temporary campaign
root was removed. No normal profile, hidden authentication state, or private
skill was used.

## Release blockers

Independent review classified three High release blockers:

1. A read-only live metadata check found the public GitHub description still
   uses the unsupported phrase `Production-grade agentic software engineering
   toolkit for OpenAI Codex.` This contradicts the WS9 public-claim boundary
   and requires an explicitly authorized remote metadata change.
2. Tracked release truth is internally stale: plugin metadata and README remain
   v0.2 alpha, README treats an obsolete BLOCKED v0.2 checklist as a current
   source, and ROADMAP still says the verified 45-run campaign is incomplete.
   Fixing these surfaces creates a new candidate and requires affected gates to
   rerun.
3. The exact candidate has no remote-tracking branch and a read-only Actions
   lookup returned no run. The repository's current release policy requires
   fresh exact-closure CI; fresh local PASS evidence is not relabeled as remote
   CI.

Independent final review: BLOCKED. It found no separate runtime, security,
benchmark, lifecycle, asset, reviewer, or presentation-evidence defect.

## Evidence-only closure boundary

This record and `docs/release/v1.0-readiness.md` are evidence-only successors to
the tested content candidate. The closure commit must change only allowed
evidence/release paths and must show zero diff in runtime-critical trees. Its
exact SHA is recorded in the final handoff rather than self-referenced here.

No remote mutation, push, merge, publish, tag, release, or submission occurred.

## Decision

WS9 is not closed. The final release gate decision is:

`NOT_RELEASE_READY`
