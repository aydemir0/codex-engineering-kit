# Codex CLI 0.147.0 Compaction Lifecycle Acceptance Evidence

Date: 2026-09-03
Platform: Windows / PowerShell
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit under test: `5393e56bedceeca1d9c672b7384a59526e0936b2`
Plugin version: `0.2.0-alpha.1`
Codex runtime: `codex-cli 0.147.0`

## Scope

This record captures only the real-runtime Phase B4 compaction lifecycle slice that was actually observed. It does not close SessionEnd timeout behavior or native subagent lifecycle acceptance.

Observed in one clean Codex 0.147.0 session:

- initial `SessionStart(source="startup")`;
- manual `/compact` lifecycle;
- `PreCompact(trigger="manual")`;
- `PostCompact(trigger="manual")`;
- deferred `SessionStart(source="compact")` on the next turn;
- compact continuation context populated from `.codex-kit/hooks/compact-state.json`;
- graceful `SessionEnd`;
- one session ID across the full lifecycle;
- workspace remained clean because hook state is gitignored.

## Operator sequence

The clean 0.147.0 runtime was started in the repository workspace with the installed Codex Engineering Kit plugin. The operator first sent a simple turn, then invoked the native TUI command:

```text
/compact
```

Codex reported:

```text
Context compacted
```

A new turn was then sent so the pending compact-start lifecycle could dispatch. Codex displayed the SessionStart hook context with a compaction continuation message indicating the prior turn and manual trigger.

The session was then exited gracefully.

## Sanitized event sequence

The raw local `.codex-kit/hooks/events.jsonl` contained this exact event order under one session identity:

```text
SessionStart source=startup
PreCompact trigger=manual
PostCompact trigger=manual
SessionStart source=compact
SessionEnd
```

The `PreCompact` and `PostCompact` events shared the same compaction turn identity.

Consistency check:

```text
Unique session IDs: 1
```

## Compact checkpoint

`.codex-kit/hooks/compact-state.json` existed after the run and recorded bounded lifecycle metadata only:

```text
sessionId=<ephemeral session id>
turnId=<ephemeral compact turn id>
trigger=manual
```

No raw transcript or prompt content is stored in this checkpoint.

The subsequent compact-source SessionStart hook read this checkpoint and emitted bounded continuation context. The observed TUI context stated that Codex Engineering Kit was resuming after compaction from the prior turn with trigger `manual`.

## Workspace cleanliness

After graceful exit:

```text
git status --short
(no output)
```

The runtime files remained outside Git tracking as designed.

## Raw artifact integrity

Ephemeral runtime identifiers are intentionally not committed. The following SHA-256 values bind this sanitized record to the local artifacts observed at acceptance time:

### `.codex-kit/hooks/events.jsonl`

```text
D8194492049F296F44E97F914BCBA8F584ADEDDF913728E0CF0DB61A8B32CF73
```

### `.codex-kit/hooks/compact-state.json`

```text
5A0B35EFFFFC11BCD0A46B7132473A6146C5CDAE8DA30C4E753D9E62549E05D9
```

### `.codex-kit/hooks/session-end.json`

```text
D69BE57ABC45588F0F95136E5606DA69B5F9FB51B00E5CF448B8365D83F903BD
```

## Phase status

This evidence supports the following Phase B4 acceptance items on real Codex CLI 0.147.0:

- `PreCompact` execution;
- `PostCompact` execution;
- manual compaction trigger propagation;
- `SessionStart(source="compact")` round trip;
- compact checkpoint persistence and bounded continuation context;
- graceful `SessionEnd` observation in the same session.

The following B4 requirements remain open and must not be promoted as complete from this record:

- `SessionEnd` timeout-budget behavior;
- `SubagentStart`;
- `SubagentStop`.

Native subagent events must be proven only after the repository has a real Codex native-subagent vertical slice; standalone dispatcher invocation is not acceptable evidence.