# Codex Desktop bundled CLI 0.152.0 compatibility acceptance

## Scope

This record captures an operator-assisted compatibility campaign for the Codex Engineering Kit v0.2 native plugin and lifecycle hooks against the Codex Desktop bundled Windows CLI runtime.

This was **not** a single-session run. A `collaborationwait_agent` call remained stuck after the reviewer had already completed, so the operator interrupted/re-entered Codex and completed the remaining compaction acceptance in later sessions. The evidence below therefore records a three-session compatibility campaign and does not claim a single uninterrupted session.

## Runtime provenance

- Platform: Windows x64
- Runtime: `codex-cli 0.152.0`
- Bundled executable: `C:\Users\aydin\AppData\Local\OpenAI\Codex\bin\7537f22ba194f7c1\codex.exe`
- Executable SHA-256: `E46F188BB3FA90FE3E05835401FACCE253CA0442E30F4B69F170BE696B43F3EC`
- Executable length: `293066544` bytes
- Exactly one local Desktop 0.152.0 candidate was found in the searched roots.

## Plugin visibility

The bundled 0.152.0 CLI reported the installed CEK plugin as:

- name: `codex-engineering-kit`
- marketplace: `codex-engineering-kit-dev`
- enabled: `True`

## Compatibility behaviors observed

The campaign observed the following native behaviors through CEK's real hook dispatcher:

1. `SessionStart(source="startup")` executed and injected the bounded CEK lifecycle context.
2. A normal `git status --short` shell call produced `PreToolUse(decision="allow")` followed by matching `PostToolUse`.
3. The acceptance-only safe deny fixture `echo CEK_HOOK_DENY_FIXTURE` produced `PreToolUse(decision="deny", fixture="acceptance")` and the UI showed deterministic blocked feedback.
4. The native custom `reviewer` subagent produced one `SubagentStart` and one `SubagentStop` with one unique agent ID.
5. Manual compaction produced `PreCompact(trigger="manual")` and `PostCompact(trigger="manual")` for the same compaction turn.
6. The next post-compaction turn produced `SessionStart(source="compact")` and CEK restored its bounded continuation context.
7. `SessionEnd` was recorded for each of the three sessions used in this campaign.
8. Repository working tree remained clean at the end (`git status --short` returned no entries).

## Event summary

Sanitized counts from the final `events.jsonl` artifact:

| Event | Count |
| --- | ---: |
| PostCompact | 1 |
| PostToolUse | 3 |
| PreCompact | 1 |
| PreToolUse | 6 |
| SessionEnd | 3 |
| SessionStart | 4 |
| SubagentStart | 1 |
| SubagentStop | 1 |

Additional invariants:

- unique sessions: `3`
- `SubagentStart`: `1`
- `SubagentStop`: `1`
- unique reviewer agent IDs: `1`

## Artifact integrity

- `.codex-kit/hooks/events.jsonl` SHA-256: `AB2D6C18798FFE5E4DE376A89969BC6595B6E1A6A650B18851603BAD22258D41`
- `.codex-kit/hooks/compact-state.json` SHA-256: `9E12DF32397BF244DAA1AFFBE320BAE4EB0A4B222E4DD05EAC71533841306E1F`
- `.codex-kit/hooks/session-end.json` SHA-256: `41C5D8EE1F3539A59D15E3C64F1A1465900A600BD0C9CDB0E460DE6CFB566D81`

The raw local artifacts contain ephemeral session/turn/tool identifiers and are therefore represented here by sanitized summaries plus SHA-256 bindings rather than copied verbatim.

## Isolated SessionEnd timeout follow-up

A separate B5 probe then exercised the existing acceptance-only SessionEnd delay fixture with:

```text
CEK_HOOK_ACCEPTANCE=1
CEK_HOOK_ACCEPTANCE_SESSION_END_DELAY_MS=5000
```

while the shipped SessionEnd hook remained configured with:

```text
timeout: 1
async: false
```

The deterministic watcher observed the fixture start marker but no subsequent normal SessionEnd record within eight seconds:

```text
MARKER UTC: 10:44:20.630
NORMAL SESSION END NOT SEEN WITHIN 8 SECONDS
```

After exit, `.codex-kit/hooks/session-end.json` did not exist. The raw timeout-probe `events.jsonl` SHA-256 was:

```text
3EF9CBDFA4A2DA12DACB5557F7FC383D65BE9323F11774F820C8425B3D04D88C
```

This differs from Windows Codex 0.147.0, where the same 5000 ms fixture completed normally despite `timeout: 1`. Full timeout evidence is recorded in `codex-desktop-0.152.0-session-end-timeout-acceptance.md`.

## Compatibility conclusion

For this operator-assisted Windows campaign, Desktop bundled Codex 0.152.0 demonstrated compatibility with the CEK v0.2 plugin for:

- plugin visibility/enabled state,
- `SessionStart`,
- normal `PreToolUse` / `PostToolUse`,
- deterministic acceptance-only deny behavior,
- native custom reviewer discovery and `SubagentStart` / `SubagentStop`,
- manual `PreCompact` / `PostCompact`,
- post-compaction `SessionStart(source="compact")`,
- graceful `SessionEnd` recording,
- enforcement of the configured SessionEnd timeout in the isolated 5000 ms delay fixture.

The Windows 0.147.0 timeout discrepancy remains a separate version-scoped limitation and must stay explicit in the compatibility matrix/release evidence.

This evidence still does not close RISK-001: the explicit plugin-manifest `hooks` override remains untested. CEK continues to rely on the default `hooks/hooks.json` discovery path.
