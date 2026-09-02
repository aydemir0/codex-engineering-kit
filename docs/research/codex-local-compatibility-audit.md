# Local Codex Compatibility Audit

Date: 2026-09-02
Status: evidence input for the v0.2 design; not an implementation claim

## Purpose

Record locally verified Codex capabilities that materially affect the Codex Engineering Kit v0.2 architecture. Machine-specific usernames, credentials, and volatile cache paths are intentionally omitted from this public document.

## Verified environment facts

- The terminal-resolved Codex CLI is 0.147.0.
- Codex Desktop bundles a newer 0.152.0 CLI.
- This version skew is useful for compatibility testing and must not be hidden by documentation.

## Verified capability surface

The local installation reports support for:

- skills
- plugins
- local plugin marketplaces
- MCP
- `codex exec`
- hooks at parser/schema level
- custom subagents at parser/discovery level
- worktree-aware behavior

Recognized hook events include:

- SessionStart
- SessionEnd
- PreToolUse
- PostToolUse
- PreCompact
- PostCompact
- SubagentStart
- SubagentStop
- PermissionRequest
- UserPromptSubmit
- Stop
- Interrupt

The native plugin manifest path is `.codex-plugin/plugin.json`.

The native custom-agent discovery path is `.codex/agents/*.toml`.

## Marketplace behavior

Verified CLI surfaces include:

```text
codex plugin list
codex plugin list --json
codex plugin list --available --json
codex plugin marketplace list
codex plugin marketplace add <local-path>
codex plugin add <plugin>@<marketplace>
```

Local marketplace manifests use `.agents/plugins/marketplace.json`.

There is no verified standalone `codex plugin enable` or `codex plugin disable` command in this installation. Enabled plugin state is represented in Codex configuration, and `codex plugin add` installs the observed plugin as enabled.

## Interfaces that must not be invented

The audit did not verify a top-level `codex skills` command, `codex config` command, or `codex worktree` command.

Binary strings alone are not sufficient evidence that `/skills`, `/plugins`, `/mcp`, or `/config` are user-facing TUI commands. Public documentation for this project must not claim those commands without an acceptance test.

## Unverified runtime boundaries

Although the parser recognizes the required hook events, actual hook execution and payload contracts have not yet been exercised with a controlled fixture.

Although `.codex/agents/*.toml` is discoverable by the engine, end-to-end spawning of a custom agent has not yet been exercised with a fixture.

These are blocking acceptance tests for v0.2, not implementation assumptions.

## Compatibility risks

### Version skew

Terminal 0.147.0 and Desktop 0.152.0 may differ in behavior. v0.2 should maintain an explicit compatibility matrix rather than silently assuming the newest Desktop behavior exists in the terminal CLI.

### CODEX_HOME isolation

Tests that rely on user configuration must control `CODEX_HOME` explicitly. Disposable acceptance tests should use a temporary Codex home so plugin, agent, hook, and marketplace tests do not mutate a real profile.

### Read operations may write housekeeping state

Nominally read-only Codex commands may perform temporary/cache housekeeping. Acceptance tests should snapshot disposable state before and after commands instead of assuming reads are filesystem-pure.

### Worktrees are an integration capability

Do not document a nonexistent `codex worktree` command. Worktree support should be tested through Git worktrees plus Codex behavior.

## Required acceptance fixtures

Before v0.2 can claim native integration, the project must demonstrate:

1. plugin install through a disposable local marketplace
2. plugin discovery/listing and removal behavior
3. one minimal custom subagent becoming spawnable
4. harmless sentinel hooks for the required lifecycle events
5. a real PreCompact/PostCompact round-trip
6. SubagentStart/SubagentStop observation
7. isolated `CODEX_HOME` behavior
8. linked Git worktree behavior
9. compatibility results for terminal 0.147.0 and Desktop 0.152.0

## Design consequences

- Keep both local Codex versions for now; they provide a useful compatibility pair.
- Do not upgrade the terminal CLI until the 0.147.0 baseline tests are captured.
- Treat hooks and agents as supported-but-not-yet-accepted until controlled runtime tests pass.
- Update public docs to use verified `codex plugin ...` commands rather than guessed slash commands.
- Make disposable `CODEX_HOME` fixtures part of the integration-test architecture.
