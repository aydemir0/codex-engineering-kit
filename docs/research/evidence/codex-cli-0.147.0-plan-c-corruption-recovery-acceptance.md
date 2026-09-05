# Codex CLI 0.147.0 Plan C Corruption-Recovery Acceptance Evidence

Date: 2026-09-04
Platform: Windows / PowerShell
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit under test: `276e9922a76b9ab43d4d022f7281adb862e00b52`
Plugin version: `0.2.0-alpha.1`
Codex runtime: `codex-cli 0.147.0`

## Scope

This record captures the real-runtime Plan C corruption-recovery slice for versioned `.codex-kit` compact state. It proves only the exact invalid-JSON recovery behavior observed on Codex CLI 0.147.0.

The acceptance run intentionally corrupted the gitignored workspace checkpoint after `PostCompact` and before the deferred compact-source `SessionStart` consumed it.

## Fixture sequence

Before starting Codex, the workspace hook state directory was recreated under:

```text
.codex-kit/hooks/
```

A PowerShell background watcher observed `events.jsonl`. As soon as `PostCompact` appeared, the watcher replaced `compact-state.json` with the intentionally invalid JSON fragment:

```text
{"broken":
```

The watcher recorded the injection time as:

```text
CORRUPTED_UTC=2026-09-04T11:25:17.1864420Z
```

No tracked repository file was modified by this fixture.

## Operator sequence

The operator started the clean Codex 0.147.0 runtime, sent a normal turn, invoked:

```text
/compact
```

and then sent the first post-compaction turn.

Codex displayed the project hook context:

```text
Codex Engineering Kit lifecycle hooks are active for this workspace. Previous compact checkpoint was invalid; continuing without restored checkpoint.
```

The user-visible completion marker was:

```text
PLAN_C_CORRUPTION_RECOVERED
```

The session then exited gracefully.

## Recovery state

The invalid compact checkpoint remained invalid after recovery; the runtime did not silently rewrite or reinterpret the corrupted artifact.

`state-recovery.json` contained:

```json
{"file":"compact-state.json","kind":"state-recovery","reason":"invalid-json","schemaVersion":1}
```

The deterministic validation reported:

```text
schemaVersion: 1
kind         : state-recovery
file         : compact-state.json
reason       : invalid-json
Recovery contract valid: True
Compact remains invalid: True
```

A normal versioned graceful-exit snapshot was still produced:

```json
{"event":"SessionEnd","kind":"session-end","schemaVersion":1,"sessionId":"<redacted>"}
```

## Lifecycle evidence

All lifecycle records used one session identity. Sanitized order:

```text
SessionStart source=startup
PreCompact trigger=manual
PostCompact trigger=manual
SessionStart source=compact
SessionEnd
```

The compact-source `SessionStart` therefore handled the corrupted checkpoint without aborting the session, emitted bounded recovery context, and continued to graceful `SessionEnd`.

## Raw artifact integrity

Ephemeral runtime identifiers are not committed. The observed local artifacts were bound by SHA-256:

### `.codex-kit/hooks/events.jsonl`

```text
D52DEF00D78672B3E66B1889A1D8941EBDCE8613BBB83CD6F28E7CE43C2EA4D0
```

### `.codex-kit/hooks/compact-state.json`

```text
CBDF3B1F91AE32FE1EA292AC6CCCF19222F97929F531523F0D15D885052C00C4
```

### `.codex-kit/hooks/state-recovery.json`

```text
6883CC371C16F91D6F21552BC000E8572A912C96D07CA42A5179F07E0F1C80A9
```

### `.codex-kit/hooks/session-end.json`

```text
2B0346E7C5E9288FBE097CDD2A88A4C275F6E1D145FB4E80A18E647EC8989EDE
```

## Workspace cleanliness

After the acceptance run:

```text
git status --short
(no output)
```

Only gitignored runtime state was touched.

## Plan C status contribution

Together with the separate Plan C read-only subagent/state/compaction acceptance, this evidence supports the corruption-recovery requirement in the Plan C slice on Codex CLI 0.147.0.

This record does not change the separate Codex 0.147.0 SessionEnd timeout discrepancy and does not close RISK-001 or RISK-002.
