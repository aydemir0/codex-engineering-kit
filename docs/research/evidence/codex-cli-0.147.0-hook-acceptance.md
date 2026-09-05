# Codex CLI 0.147.0 Native Hook Acceptance Evidence

Date: 2026-09-03
Platform: Windows / PowerShell
Repository branch: `feat/codex-native-plugin-v0.2`
Repository commit under test: `9378051199e970677ebe4c8b83c625c39e4f8c91`
Plugin version: `0.2.0-alpha.1`
Codex runtime: `codex-cli 0.147.0`

## Scope

This record closes only the real-runtime hook behavior that was actually observed for Phase B3. It does not close compaction or subagent lifecycle acceptance.

Observed on a clean, separately installed `@openai/codex@0.147.0` Windows runtime:

- plugin visibility through the configured local marketplace;
- default plugin hook discovery through `hooks/hooks.json`;
- operator-visible hook trust/review flow (observed earlier in the same 0.147 acceptance campaign; the final clean rerun reused the already trusted hook configuration);
- `SessionStart` execution and bounded additional context;
- normal `PreToolUse` allow path;
- `PostToolUse` execution for the allowed shell command;
- safe acceptance-only `PreToolUse` deny fixture;
- `SessionEnd` execution on graceful exit.

## Clean runtime prerequisite

The globally upgraded npm installation had left an incomplete legacy directory containing `codex.exe` 0.147.0 but no matching `codex-code-mode-host.exe`. That stale directory caused shell execution to fail closed and was not accepted as a valid runtime baseline.

A clean isolated install was created with:

```powershell
npm install --prefix $tmp147 --include=optional --no-save @openai/codex@0.147.0
```

The clean package contained both:

- `codex.exe`
- `codex-code-mode-host.exe`

and reported:

```text
codex-cli 0.147.0
```

No global downgrade was performed; the user's current global Codex installation remained separate.

## Acceptance sequence

The final clean run used the exact repository workspace and `CEK_HOOK_ACCEPTANCE=1` acceptance fixture.

Normal command:

```text
git status --short
```

Observed result:

```text
Ran git status --short
(no output)
```

No hook failure was reported. The hook evidence recorded the normal `PreToolUse` decision as `allow`, followed by `PostToolUse`.

Safe deny fixture:

```text
echo CEK_HOOK_DENY_FIXTURE
```

Observed result:

```text
PreToolUse hook (blocked)
feedback: Blocked by Codex Engineering Kit acceptance fixture.
```

The sentinel is acceptance-only and requires `CEK_HOOK_ACCEPTANCE=1`; it does not broaden the production destructive-command policy.

## Sanitized event sequence

The raw local `events.jsonl` contained the following sequence, all under one session ID:

```text
SessionStart source=startup
PreToolUse decision=allow toolName=Bash
PostToolUse toolName=Bash
PreToolUse decision=deny fixture=acceptance toolName=Bash
SessionEnd
```

Consistency check:

```text
Unique session IDs: 1
```

`session-end.json` was also present after graceful exit and contained the same session identity as the event stream.

The workspace remained clean:

```text
git status --short
(no output)
```

Runtime state under `.codex-kit/hooks/` therefore remained excluded from Git tracking as designed.

## Raw artifact integrity

The raw local `.codex-kit/hooks/events.jsonl` was not committed because it contains ephemeral runtime identifiers. Its SHA-256 at acceptance time was:

```text
17C6E8B8223D2F56BC7DA016C1F4D5560059162CC7D650661F1F1B2465E6DCB7
```

This hash binds this sanitized record to the operator-observed raw event artifact without publishing session/tool-use identifiers.

## Phase status

Phase B3 real Codex 0.147 acceptance is supported for:

- default hook discovery;
- trust/review boundary;
- `SessionStart`;
- normal `PreToolUse` allow behavior;
- acceptance-fixture `PreToolUse` deny behavior;
- raw evidence integrity.

`PostToolUse` and graceful `SessionEnd` were additionally observed in the same single-session run. They are useful evidence for Phase B4, but this record does not claim that B4's remaining requirements are complete. In particular, the following remain open until separately exercised on real runtimes:

- `SessionEnd` timeout-budget behavior;
- `PreCompact`;
- `PostCompact`;
- `SessionStart(source="compact")` round trip;
- `SubagentStart`;
- `SubagentStop`.

## Notes

The earlier shell failures encountered while re-running 0.147 were environmental: an incomplete npm upgrade residue lacked `codex-code-mode-host.exe`. A fresh `@openai/codex@0.147.0` install restored the matching host and the exact original shell acceptance passed without code-mode feature overrides. No CEK hook code change was required for that environmental issue.
