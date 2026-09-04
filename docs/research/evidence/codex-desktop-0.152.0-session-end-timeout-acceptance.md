# Codex Desktop bundled CLI 0.152.0 SessionEnd timeout acceptance

Date: 2026-09-04
Platform: Windows x64 / PowerShell
Repository branch: `feat/codex-native-plugin-v0.2`
Plugin version: `0.2.0-alpha.1`
Codex runtime: `codex-cli 0.152.0`

## Status

**CONFIRMED: Desktop bundled Windows Codex 0.152.0 enforces the configured SessionEnd timeout under the CEK acceptance fixture.**

This behavior differs materially from the separately documented official Windows Codex 0.147.0 runtime discrepancy, where the same 5000 ms acceptance delay completed normally despite `timeout: 1`.

## Runtime provenance

- Bundled executable: `C:\Users\aydin\AppData\Local\OpenAI\Codex\bin\7537f22ba194f7c1\codex.exe`
- Runtime-reported version: `codex-cli 0.152.0`
- Executable SHA-256: `E46F188BB3FA90FE3E05835401FACCE253CA0442E30F4B69F170BE696B43F3EC`
- Executable length: `293066544` bytes

The preceding B5 compatibility campaign found exactly one matching Desktop 0.152.0 candidate in the searched local runtime roots.

## CEK timeout fixture

The existing acceptance-only SessionEnd fixture was enabled with:

```text
CEK_HOOK_ACCEPTANCE=1
CEK_HOOK_ACCEPTANCE_SESSION_END_DELAY_MS=5000
```

The shipped SessionEnd hook configuration remains:

```text
timeout: 1
async: false
```

The fixture writes a metadata-only `phase=started` marker before sleeping. A normal SessionEnd record and `session-end.json` are written only after the sleep returns and normal SessionEnd handling continues.

## Deterministic watcher result

A separate PowerShell watcher polled `.codex-kit/hooks/events.jsonl` approximately every 50 ms.

Observed result:

```text
MARKER UTC: 10:44:20.630
NORMAL SESSION END NOT SEEN WITHIN 8 SECONDS
```

No normal SessionEnd event appeared after the fixture marker within the eight-second watcher window.

## Sanitized event sequence

The raw event artifact contained:

```text
SessionStart source=startup
SessionEnd fixture=session-end-timeout phase=started delayMs=5000
```

It did **not** contain the subsequent normal SessionEnd event.

After Codex returned to PowerShell:

```text
session-end.json exists: False
```

This is the expected observable outcome if the host terminates the SessionEnd hook before the five-second delay completes.

## Artifact integrity

`.codex-kit/hooks/events.jsonl` SHA-256:

```text
3EF9CBDFA4A2DA12DACB5557F7FC383D65BE9323F11774F820C8425B3D04D88C
```

The repository working tree remained clean after the probe.

## Comparison with Windows Codex 0.147.0

The same CEK acceptance fixture previously produced this deterministic 0.147.0 watcher result:

```text
DELTA MS: 4961
session-end.json exists: True
```

In contrast, Desktop bundled 0.152.0 produced:

```text
NORMAL SESSION END NOT SEEN WITHIN 8 SECONDS
session-end.json exists: False
```

Therefore the two Windows baselines do not have equivalent SessionEnd timeout behavior under the same CEK acceptance fixture:

- Windows Codex 0.147.0: configured one-second timeout was not observably enforced in the acceptance run.
- Desktop bundled Windows Codex 0.152.0: configured one-second timeout was observably enforced before the five-second fixture completed.

## Gate disposition

For the tested Desktop bundled Windows Codex 0.152.0 runtime, the SessionEnd timeout-budget acceptance gate is **PASS** for this fixture.

The broader compatibility statement remains version-scoped. CEK must preserve the Windows 0.147.0 limitation separately and must not generalize 0.152.0 behavior to all platforms or later runtimes without corresponding evidence.

RISK-001 remains unrelated and open: explicit plugin-manifest `hooks` override behavior was not tested by this probe.
