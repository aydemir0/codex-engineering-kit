# Codex CLI 0.147.0 SessionEnd Timeout Compatibility Discrepancy

Date: 2026-09-03
Platform: Windows / PowerShell
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit under test: `377ea417fda47f81f1d95320ba0e0bf32de2b711`
Plugin version: `0.2.0-alpha.1`
Codex runtime reported by binary: `codex-cli 0.147.0`

## Status

**OPEN compatibility discrepancy.**

This record does **not** close the Phase B4 `SessionEnd` timeout-budget acceptance gate.

The real Windows Codex 0.147.0 runtime allowed an acceptance-only SessionEnd fixture configured to delay for 5000 ms to complete normally even though the shipped plugin configuration declares `timeout: 1` for SessionEnd.

The result is recorded as observed runtime behavior, not as a claim about all Codex 0.147.0 builds or platforms.

## CEK configuration under test

`hooks/hooks.json` declares the SessionEnd command hook with:

```text
timeout: 1
async: false
```

The repository and installed plugin-cache copies were checked before the acceptance run.

### `hooks/hooks.json` SHA-256

Repository:

```text
5FA7D8499C9A151284A43619F57CF53AFE88B907A3AD392E2942DBF6FCF44E5B
```

Plugin cache:

```text
5FA7D8499C9A151284A43619F57CF53AFE88B907A3AD392E2942DBF6FCF44E5B
```

Result: exact match.

### `hooks/scripts/hook_dispatch.py` SHA-256

Repository:

```text
DE76E4F744EAD6D2EFEE75859D5646B7880902611783FAD7BCFFE6C327F09133
```

Plugin cache:

```text
DE76E4F744EAD6D2EFEE75859D5646B7880902611783FAD7BCFFE6C327F09133
```

Result: exact match.

## Acceptance-only timeout fixture

The dispatcher fixture activates only when:

```text
CEK_HOOK_ACCEPTANCE=1
CEK_HOOK_ACCEPTANCE_SESSION_END_DELAY_MS=<bounded integer>
```

For this run the delay was:

```text
5000 ms
```

The fixture first appends a metadata-only marker:

```text
SessionEnd fixture=session-end-timeout phase=started delayMs=5000
```

It then sleeps for the configured duration before writing the normal bounded SessionEnd snapshot and normal SessionEnd event.

Production behavior remains unchanged when acceptance mode is disabled.

## Deterministic watcher result

A separate PowerShell watcher polled `.codex-kit/hooks/events.jsonl` approximately every 50 ms, eliminating operator typing latency from the measurement.

Observed timestamps:

```text
MARKER UTC: 12:56:55.315
NORMAL UTC: 12:57:00.276
DELTA MS: 4961
```

The approximately five-second delta matches the acceptance fixture delay rather than the declared one-second SessionEnd timeout.

## Sanitized event sequence

The raw local event stream contained one session identity with this sequence:

```text
SessionStart source=startup
SessionEnd fixture=session-end-timeout phase=started delayMs=5000
SessionEnd
```

After exit:

```text
session-end.json exists: True
```

The completed normal SessionEnd event and snapshot show that the dispatcher reached the code after the five-second sleep.

## Orphan-process hypothesis

A prior diagnostic probe checked for a surviving Python hook process immediately after Codex returned to PowerShell and again six seconds later.

Observed:

```text
normal SessionEnd already present at first check
session-end.json exists: True
hook_dispatch.py Python process: none observed
state unchanged six seconds later
```

This did not support the hypothesis that Codex timed out a shell wrapper while an orphaned Python grandchild continued in the background.

## First-party source contract checked

The exact `rust-v0.147.0` OpenAI Codex source was reviewed during diagnosis.

Relevant first-party paths:

- `codex-rs/config/src/hook_config.rs`
  - JSON field `timeout` deserializes into command-hook `timeout_sec`.
- `codex-rs/hooks/src/engine/discovery.rs`
  - SessionEnd timeout normalization defaults to one second and clamps configured values to the documented bounded range.
- `codex-rs/hooks/src/engine/command_runner.rs`
  - command execution is wrapped in `tokio::time::timeout(Duration::from_secs(handler.timeout_sec), ...)`.
- `codex-rs/core/src/hook_runtime.rs`
  - root SessionEnd execution awaits `hooks.run_session_end(request)` during shutdown.

The observed local runtime behavior therefore conflicts with the expected source-level timeout contract under this Windows acceptance setup.

This record does not yet establish whether the discrepancy comes from binary/package provenance, build differences, or another runtime condition not visible from repository-side configuration.

## Raw artifact integrity

The final deterministic watcher run produced `.codex-kit/hooks/events.jsonl` SHA-256:

```text
270E4CC264527CED1DEB936706014538EA2E892E21392807F3626C2F1696642C
```

Ephemeral session identifiers are intentionally omitted from this committed evidence file.

## External release provenance reference

The official OpenAI Codex `rust-v0.147.0` GitHub release publishes a Windows x86_64 executable asset named:

```text
codex-x86_64-pc-windows-msvc.exe
```

GitHub reports the release asset SHA-256 as:

```text
935a1911ed2556e4ffcec995f4886ac2ac425863ba26fed264df62e30272ad9d
```

A local hash comparison against the npm-installed acceptance binary remains the next diagnostic step. Until that comparison is made, this document must not claim the local binary is byte-for-byte identical to the standalone release asset.

## Gate status

Confirmed on real Windows Codex CLI reporting version 0.147.0:

- SessionEnd hook executes;
- acceptance-only delay fixture executes;
- repository and plugin-cache hook configuration are identical;
- repository and plugin-cache dispatcher are identical;
- a 5000 ms delay completes normally;
- deterministic watcher observes approximately 4961 ms from fixture marker to normal SessionEnd;
- normal SessionEnd snapshot is written.

Not confirmed / remains open:

- enforcement of the configured one-second SessionEnd timeout on this runtime;
- byte-for-byte provenance match between the npm-installed binary and official standalone Windows release asset;
- whether the same discrepancy reproduces on Desktop 0.152.0, macOS, or Linux.

Therefore the v0.2 `SessionEnd meets timeout budget` acceptance item remains **OPEN**.