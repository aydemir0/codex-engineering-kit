# Codex CLI 0.147.0 Plan C State + Native Subagent Acceptance Evidence

Date: 2026-09-04
Platform: Windows / PowerShell
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit under test: `8c3351c83e59bec2d38c5bab774534cf06404271`
Plugin version: `0.2.0-alpha.1`
Codex runtime: `codex-cli 0.147.0`

## Scope

This record captures the real-runtime Plan C acceptance slice for the current versioned state runtime and native custom-agent configuration.

It supports only behavior directly observed in this operator-assisted run. It does not claim that read-only agent instructions are a sandbox, and it does not close broader worktree or controlled-write execution acceptance.

## Repository and plugin state

The working branch was fast-forwarded to the commit under test and remained clean before runtime acceptance.

The project-level agent configuration was present as:

```toml
[agents]
max_concurrent_threads_per_session = 4
```

The following custom agent files were present:

```text
architect.toml
build-resolver.toml
docs-researcher.toml
e2e-runner.toml
explorer.toml
refactor-cleaner.toml
reviewer.toml
security-reviewer.toml
```

The plugin cache was refreshed through the repo-local marketplace flow before acceptance.

Repository and installed-cache dispatcher SHA-256 values matched exactly:

```text
612578F9DCB73A96E8BF8FF3F4D4B8BA5E17AAE527BCC40582D0BAC0CF8FD6BC
```

Repository and installed-cache `runtime/state.py` SHA-256 values also matched exactly:

```text
174577DAE3A9476B88A6D87CDAE5BC2416E07FABD2546C219C0838F8179651E2
```

The operator transcript captured identical repository/cache state hashes; the final echoed boolean for the state hash comparison was not retained in the pasted transcript, so this record binds only the observed identical hash values rather than inventing an omitted console line.

## Native explorer acceptance

The operator instructed Codex to use the custom `explorer` role for a read-only inspection of `runtime/state.py` and return `SCHEMA_VERSION`.

The first spawn-tool attempt was rejected before agent creation because that invocation combined a custom agent type with full-history transfer. Codex explicitly reported that no agent was created and retried without the incompatible history-transfer option.

The accepted retry produced exactly one real custom-agent lifecycle pair:

```text
SubagentStart agentType=explorer
SubagentStop  agentType=explorer
```

Both events carried the same ephemeral agent identity in the raw local artifact.

The explorer result returned:

```text
PLAN_C_EXPLORER_DONE schema=1
```

The raw event stream also contained the child agent's local tool events. Those are intentionally omitted from this sanitized summary; the stable acceptance claim is the custom `explorer` lifecycle and its bounded result.

## Compaction round trip with versioned state

After the explorer completed, the same Codex session exercised native manual compaction.

Sanitized lifecycle order:

```text
SessionStart source=startup
SubagentStart agentType=explorer
SubagentStop agentType=explorer
PreCompact trigger=manual
PostCompact trigger=manual
SessionStart source=compact
SessionEnd
```

`PreCompact` and `PostCompact` shared the same compaction turn identity, and `SessionStart(source="compact")` resumed under the same session identity.

Codex displayed bounded continuation context indicating that the session was resuming from the prior manual compaction turn.

## Versioned state artifacts

`.codex-kit/hooks/compact-state.json` existed after the run and contained:

```text
kind=compact-checkpoint
schemaVersion=1
trigger=manual
```

`.codex-kit/hooks/session-end.json` existed after graceful exit and contained:

```text
kind=session-end
schemaVersion=1
event=SessionEnd
```

No raw prompt or transcript body is part of these state records.

## Raw artifact integrity

Ephemeral runtime identifiers are intentionally not committed. The following SHA-256 values bind this sanitized record to the operator-observed local artifacts.

### `.codex-kit/hooks/events.jsonl`

```text
AA49C4C65CF3D3EA6174AFE66EAC713686CDB77B21A3AC5C1187280CBAF2A830
```

### `.codex-kit/hooks/compact-state.json`

```text
689A398B9E34126A4074A95542A8AACF8B52DBE519FAE366B5D9D5F03A4E475C
```

### `.codex-kit/hooks/session-end.json`

```text
5059261A81F88F7794078B8A28BA217E71437FF2DC4EC5619902B45BC22E1E83
```

## Workspace cleanliness

After graceful exit:

```text
git status --short
(no output)
```

Runtime state therefore remained excluded from Git tracking as designed.

## Acceptance status

This real Codex CLI 0.147.0 run supports the following Plan C behavior at commit `8c3351c83e59bec2d38c5bab774534cf06404271`:

- project agent configuration is present with a concurrency cap of four;
- the current repo/cache dispatcher and state runtime bytes are aligned;
- a real custom read-only `explorer` agent loads and produces one observed `SubagentStart` / `SubagentStop` pair;
- the explorer returns the expected versioned-state value `SCHEMA_VERSION = 1`;
- manual compaction persists versioned bounded checkpoint state;
- `SessionStart(source="compact")` restores bounded continuation context;
- graceful `SessionEnd` writes versioned bounded state;
- the workspace remains clean after the runtime lifecycle.

The first failed spawn-tool attempt is retained as an acceptance nuance: it failed before agent creation because of an incompatible history-transfer option. It does not invalidate the one successfully observed explorer lifecycle, but future deterministic acceptance prompts should avoid requesting full-history transfer for a typed custom agent.

## Remaining Plan C check

Corruption recovery is covered by repository tests but is not claimed as real-runtime accepted by this record. A separate safe corruption-recovery acceptance probe should exercise a deliberately malformed local `.codex-kit/hooks/compact-state.json` and verify bounded recovery behavior without modifying tracked repository files.
