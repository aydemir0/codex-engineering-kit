# Gemini Official-Docs Reconciliation

Date: 2026-09-02
Status: research synthesis for v0.2; official OpenAI docs and local Codex evidence take precedence over model-generated claims

## Purpose

The Gemini reconnaissance covered the right surfaces—plugins, marketplaces, skills, custom subagents, hooks, MCP, worktrees, non-interactive execution, testing, and publication—but several claims conflict with either the current official OpenAI documentation or the locally verified Codex installation. This document records what is accepted, corrected, or left for acceptance testing.

## Accepted findings

- Native plugin manifests live at `.codex-plugin/plugin.json`.
- A plugin can package skills and may bundle lifecycle hooks and MCP metadata.
- Local/repo marketplaces use `.agents/plugins/marketplace.json`.
- ChatGPT and Codex share a universal public plugin directory.
- Project-scoped custom agents live under `.codex/agents/*.toml`.
- `name`, `description`, and `developer_instructions` are required custom-agent fields.
- Hooks require explicit trust when unmanaged; plugin installation/enabling does not automatically trust bundled hooks.
- `PreToolUse` can deny supported tool calls and can rewrite supported inputs only when allowing the call.
- `SessionStart` can inject bounded developer context and can run again after compaction with source `compact`.
- `PreCompact` and `PostCompact` are first-class lifecycle events.
- `codex exec` is the non-interactive automation surface.
- Worktree-aware workflows are a real Codex capability and are appropriate for isolated write tracks.

## Corrections

### Plugin CLI spelling

The reconnaissance used `codex plugins install ...` in one section. The local installation verified the singular command family:

```text
codex plugin list
codex plugin marketplace add <source>
codex plugin add <plugin>@<marketplace>
```

Public project docs will use commands proven by the local target versions, not guessed aliases.

### Hook composition

The reconnaissance claimed plugin hooks can shadow user hooks. Current official Hook docs state that matching hooks from multiple files all run, and multiple matching command hooks for an event may run concurrently. The shadowing claim is therefore rejected for v0.2 design purposes unless a reproducible version-specific regression is demonstrated.

### Supported hook events

The public v0.2 contract will use the events listed in current official docs:

- PreToolUse
- PermissionRequest
- PostToolUse
- PreCompact
- PostCompact
- UserPromptSubmit
- SubagentStop
- Stop
- SessionStart
- SubagentStart
- SessionEnd

The local binary also recognized `Interrupt`, but because it is not part of the current documented hook table it is treated as parser evidence only and is not a v0.2 public API dependency.

### Custom-agent model defaults

The reconnaissance said every custom agent must define its own model because no global fallback exists. Current official Subagents docs contradict that: subagents may inherit the parent model/reasoning effort, and `[agents]` supports default subagent model/reasoning settings. v0.2 will therefore avoid unnecessary hard-coded model pins in portable agent definitions.

### Hook execution model

`SessionStart` is not treated as globally asynchronous by design. Command hooks are synchronous by default unless configured with `async = true`; some lifecycle/MCP timing has special non-blocking behavior. v0.2 will rely on the event-specific official contract rather than a blanket async assumption.

### Plugin manifest `hooks` ambiguity

Current Hook docs explicitly support plugin-bundled hooks and say Codex looks for `hooks/hooks.json` by default; a manifest may override this with a `hooks` entry. The current plugin-creator sample specification contains internally inconsistent validation notes about the `hooks` manifest field. To minimize compatibility risk, v0.2 will initially use the default `hooks/hooks.json` discovery path and will only add an explicit manifest `hooks` override after acceptance tests pass on both target local versions.

### MCP key casing

The canonical plugin sample uses the manifest field `mcpServers`. Any wrapped MCP companion-file shape will be tested rather than inferred from conflicting prose. v0.2 does not need to bundle a remote MCP server to prove the core plugin architecture, so MCP packaging remains opt-in.

## Locked official-runtime details

- Plugin hooks receive `PLUGIN_ROOT` and `PLUGIN_DATA`.
- `SessionEnd` has a very short default timeout (1 second, max 3 seconds), so it may only perform cheap deterministic persistence.
- Hook model-visible output is bounded; the default additional-context threshold is approximately 2,500 tokens unless configured otherwise.
- `PreToolUse` supports `permissionDecision: "deny"` plus a reason, and `permissionDecision: "allow"` with `updatedInput` for supported rewrites.
- `permissionDecision: "ask"` is not supported for `PreToolUse` today.
- `PostToolUse` cannot undo tool side effects; it can replace/block the result path or add context after execution.
- The hook system is a guardrail, not a complete sandbox/security boundary.
- Subagent workflows consume more tokens than comparable single-agent runs, so parallelism must be bounded and justified.
- Custom agents inherit parent settings when fields such as model, sandbox, MCP, or skills are omitted.

## Local verification still required

1. Minimal plugin installation from a disposable local marketplace.
2. `/plugins` visibility and install/uninstall behavior in the real CLI/Desktop surfaces.
3. Hook trust UX for a plugin-bundled `hooks/hooks.json`.
4. Exact hook payloads on terminal 0.147.0 and Desktop 0.152.0.
5. `PreToolUse` deny behavior on both versions.
6. `SessionStart(source=compact)` and Pre/PostCompact round-trip.
7. Custom agent loading/spawn under `.codex/agents/*.toml`.
8. Subagent lifecycle hooks and bounded concurrency.
9. Plugin enabled/disabled behavior, including any version-specific remote-plugin bug.
10. MCP companion-file schema only if v0.2 actually ships an MCP integration.

## Design consequence

The implementation plan must treat official docs as the intended contract, local acceptance tests as runtime truth for supported versions, and third-party/model-generated reports as research leads rather than authority.
