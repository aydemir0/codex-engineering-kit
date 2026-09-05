# Codex CLI 0.147.0 Native Reviewer Subagent Acceptance

## Scope

This record covers the real-runtime Windows acceptance of the first Codex-native custom subagent vertical slice for Codex Engineering Kit v0.2.

It closes evidence for:

- project-local discovery of `.codex/agents/reviewer.toml`;
- a real native `reviewer` subagent lifecycle;
- `SubagentStart`;
- `SubagentStop`;
- bounded, metadata-only hook evidence for the subagent lifecycle.

It does **not** close the separate SessionEnd timeout-budget discrepancy.

## Runtime and code under test

- Codex CLI: `0.147.0`
- Platform: Windows
- Repository branch: `feat/codex-native-plugin-v0.2`
- Code-under-test head before this evidence commit: `47d0d329e71cf14331e94393ac2257f946a7cf7b`
- Reviewer role: `.codex/agents/reviewer.toml`
- Plugin version expected from `.codex-plugin/plugin.json`: `0.2.0-alpha.1`

The reviewer role is intentionally read-only and does not pin a model or reasoning level, so the native role can inherit the parent runtime configuration.

## Operator prompt

The operator asked Codex to use the custom `reviewer` subagent for exactly one focused, read-only question:

> Inspect `.codex-plugin/plugin.json` and report the plugin version with the file path as evidence.

The parent was instructed not to answer the delegated question before the reviewer returned.

## Observed TUI behavior

Sanitized observations:

1. `SessionStart` hook completed.
2. Codex announced that it was delegating the read-only check to the reviewer.
3. The TUI printed `Started /root/plugin_version_review` twice.
4. Codex waited for agents.
5. The final parent response was:

   `REVIEWER_ACCEPTANCE_DONE version=0.2.0-alpha.1`

The duplicate `Started` UI lines are not interpreted as two completed agents. Raw hook evidence below is authoritative for lifecycle counts.

Unrelated Cloudflare MCP authentication/startup warnings were present and are outside this acceptance scope.

## Sanitized hook event sequence

The raw hook artifact contained the following relevant sequence:

1. `SessionStart(source="startup")`
2. two `PreToolUse` records for `collaborationspawn_agent`
3. one `PostToolUse` record for the successful `collaborationspawn_agent` tool use
4. one `PreToolUse` for `collaborationwait_agent`
5. one `SubagentStart` with `agentType="reviewer"`
6. reviewer-local `PreToolUse` / `PostToolUse` Bash activity for read-only inspection
7. one `SubagentStop` with `agentType="reviewer"`
8. one `PostToolUse` for `collaborationwait_agent`
9. `SessionEnd`

Ephemeral session, turn, tool-use, and agent identifiers are intentionally omitted from this committed evidence.

## Lifecycle assertions

The operator-side summary over the raw JSONL reported:

- `SubagentStart: 1`
- `SubagentStop: 1`
- unique subagent IDs: `1`
- `agentType`: `reviewer`
- the `SubagentStart` and `SubagentStop` records used the same agent ID
- repository `git status --short` was clean after the run

Therefore this acceptance proves one real native reviewer lifecycle from start through stop.

### Important nuance: spawn attempts vs. actual agent lifecycle

The parent runtime emitted two `PreToolUse` events for `collaborationspawn_agent`, and the TUI displayed the same `Started /root/plugin_version_review` label twice. Only one spawn tool use produced the completed tool-use/lifecycle chain, and only one native agent ID appeared in `SubagentStart` / `SubagentStop`.

Accordingly, this evidence supports:

- **one actual native reviewer agent lifecycle**;
- **not** the stronger claim that the runtime made exactly one spawn-tool attempt.

That distinction is preserved rather than normalized away.

## Raw artifact integrity

Operator-produced SHA-256 for `.codex-kit/hooks/events.jsonl`:

`82FE31AF50DF78B056AE549DBD84877DC8BEAA14CD4B2C30B17B9CCAF305CD21`

The raw artifact remains local; this repository stores only the sanitized evidence record and its integrity binding.

## Acceptance result

### Proven on real Codex CLI 0.147.0

- project-local custom reviewer role was usable by the parent agent;
- delegated read-only inspection returned the expected plugin version;
- `SubagentStart` fired for `agentType="reviewer"`;
- `SubagentStop` fired for the same reviewer agent;
- exactly one unique reviewer agent ID completed the lifecycle;
- hook evidence remained bounded to lifecycle/tool metadata;
- repository remained clean after acceptance.

### Still open / separate

- SessionEnd configured timeout-budget enforcement on the official Windows 0.147.0 runtime remains an open compatibility discrepancy documented separately.
- Desktop bundled Codex 0.152 compatibility remains to be tested in Phase B5.

## Phase status

For Phase B4, the real-subagent requirement is now satisfied for:

- `SubagentStart`
- `SubagentStop`

The remaining B4 caveat is the already-recorded SessionEnd timeout-budget discrepancy; it is not silently treated as a pass.
