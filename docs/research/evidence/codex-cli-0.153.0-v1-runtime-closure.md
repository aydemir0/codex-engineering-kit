# Codex CLI 0.153.0 — v1 Runtime Closure Evidence

## Scope

- Runtime: Codex CLI 0.153.0
- Candidate SHA: `83823570cbfd8aa9d93dd9b0943c6a97adb38281`
- Host family: Windows
- Campaign type: fresh v1 runtime-closure acceptance
- Acceptance state: disposable runtime/profile and fixture state
- Raw machine-local logs and session identifiers are intentionally not committed.

This evidence is scoped only to Codex CLI 0.153.0 and the exact candidate SHA above.
It does not establish Codex Desktop compatibility and does not promote evidence across runtimes.

## Surface results

| Surface | Status | Observation |
| --- | --- | --- |
| `plugin-discovery` | PASS | Fresh CLI 0.153.0 plugin discovery completed successfully in the disposable campaign. |
| `marketplace-install-list` | PASS | Marketplace registration/install/list flow completed successfully on CLI 0.153.0. |
| `skill-discovery` | NOT_RUN | Direct runtime observation of project skill discovery was not established by the CLI campaign. |
| `default-hooks` | PASS | Default native `hooks/hooks.json` discovery executed the bounded lifecycle fixture. |
| `explicit-hooks` | PASS | Explicit manifest hook override executed successfully in a disposable manifest variant. |
| `hook-lifecycle` | PASS | SessionStart, PreToolUse allow/deny, PostToolUse, and graceful SessionEnd were observed within the bounded lifecycle fixture. |
| `pretool-deny-allow` | PASS | Narrow allowed command executed and the acceptance deny sentinel was blocked by PreToolUse. |
| `native-subagent` | PASS | A real project-local `explorer` subagent emitted SubagentStart and SubagentStop with matching agent identity, and the parent resumed after waiting. |
| `compaction-state` | PASS | Manual PreCompact and PostCompact were observed, schema-v1 compact checkpoint state was written, continuation succeeded after resume, and unsupported checkpoint schema failed safely. |
| `session-end` | PASS | Graceful SessionEnd was observed separately; a 2.5-second acceptance delay against the 1-second SessionEnd hook budget was predictably timed out without producing a false completed SessionEnd snapshot. |
| `interactive-plugin-discovery` | NOT_RUN | No separate interactive plugin-discovery acceptance was classified in this campaign. |
| `desktop-parent-wait` | NOT_RUN | Desktop-specific surface; not applicable to the CLI 0.153.0 baseline. |

## Hook trust boundary

Both default-hook discovery and the disposable explicit-manifest hook path passed with persisted operator trust and without the hook-trust bypass flag.

This proves the CLI 0.153.0 hook paths tested here. It does not establish the same behavior on Codex Desktop.

## Native subagent boundary

The project-local `explorer` lifecycle was observed with:

- SubagentStart
- SubagentStop
- matching agent identity
- parent continuation after waiting

The exact child response text was not observed in the root `codex exec --json` stream, so this evidence does not claim that exact child text propagation was proven.

## Compaction boundary

The successful manual compaction path observed:

- PreCompact with trigger `manual`
- PostCompact with trigger `manual`
- checkpoint schema version `1`
- checkpoint kind `compact-checkpoint`
- successful model continuation after resuming the same compacted session

For this manual compact-and-resume path, `SessionStart source=compact` was not observed. The resumed process emitted `SessionStart source=resume`. This is recorded as an observed runtime-path distinction, not promoted into a `SessionStart source=compact` claim.

A separate deterministic state-handler acceptance used an unsupported schema version and confirmed:

- recovery record creation
- reason `unsupported-schema`
- invalid checkpoint not restored
- safe continuation context

## SessionEnd timeout boundary

The timeout fixture injected a 2500 ms SessionEnd delay while the CEK manifest allowed 1 second for SessionEnd.

Observed:

- timeout fixture start event recorded
- normal completed SessionEnd event not recorded
- final `session-end.json` snapshot not produced

Graceful SessionEnd and timeout behavior were tested separately.

## Known limitations

- Codex Desktop 0.152.0 required runtime surfaces remain separately blocked/unavailable in this campaign.
- `skill-discovery` remains NOT_RUN for CLI 0.153.0.
- `interactive-plugin-discovery` remains NOT_RUN for CLI 0.153.0.
- `SessionStart source=compact` was not observed in the successful manual compact-and-resume path.
- No blanket cross-platform or Desktop compatibility claim is made from this CLI evidence.