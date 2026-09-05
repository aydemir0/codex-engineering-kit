# Codex CLI 0.147.0 — Sanitized Raw Evidence

Date captured: 2026-09-03
Source: local Windows installation
Purpose: raw-evidence gate for Codex Engineering Kit v0.2 design

The original local capture is intentionally not committed because it contains machine-specific user/cache paths and installed-plugin inventory. This document preserves the technical evidence needed for the design while redacting personal and volatile paths.

Original local capture SHA-256:

```text
73fe8e5030ff22b1246b9896dc1eca7a299b79d4a79296bd15c6c0f74ab4634b
```

## 1. Version

Command:

```text
codex --version
```

Observed output:

```text
codex-cli 0.147.0
```

Status: VERIFIED on the terminal-resolved CLI.

## 2. Plugin listing

Command:

```text
codex plugin list --json
```

Observed behavior:

- command completed and returned structured JSON
- response contained an `installed` array
- installed entries exposed `pluginId`, `name`, `marketplaceName`, `version`, `installed`, `enabled`, `source`, `marketplaceSource`, `installPolicy`, and `authPolicy`
- observed installed entries were `installed: true` and `enabled: true`
- response also contained an `available` array
- in this capture, `available` was empty

Machine-specific plugin paths and the complete installed-plugin inventory are omitted from this public evidence file.

Status: VERIFIED.

## 3. Marketplace listing

Command:

```text
codex plugin marketplace list --json
```

Observed behavior:

- command completed and returned structured JSON
- response contained a `marketplaces` array
- three marketplace registrations were present in the local profile
- each entry exposed a marketplace `name` and local `root`

The local root paths are omitted because they include user-specific and volatile cache locations.

Status: VERIFIED.

## 4. Local/Git marketplace registration surface

Command:

```text
codex plugin marketplace add --help
```

Observed help text:

```text
Add a local or Git marketplace to the configured marketplace sources

Usage: codex plugin marketplace add [OPTIONS] <SOURCE>

Arguments:
  <SOURCE>
          Marketplace source: a local path, owner/repo[@ref], HTTPS Git URL, or SSH Git URL
```

Observed examples:

```text
codex plugin marketplace add ./path/to/marketplace
codex plugin marketplace add owner/repo --ref main
codex plugin marketplace add https://github.com/owner/repo --sparse plugins/foo
```

Observed relevant options included:

```text
--ref <REF>
--sparse <PATH>
--json
```

Status: VERIFIED.

## 5. Feature flags relevant to v0.2

Command:

```text
codex features list
```

Observed relevant entries:

```text
hooks                                stable             true
memories                             stable             true
multi_agent                          stable             true
plugin_hooks                         removed            false
plugin_sharing                       stable             true
plugins                              stable             true
remote_compaction_v2                 stable             true
skill_mcp_dependency_install         stable             true
skill_search                         stable             true
workspace_dependencies               stable             true
```

Interpretation boundaries:

- `hooks stable true` verifies the general hooks feature is enabled in this CLI build.
- `multi_agent stable true` verifies the current multi-agent feature is enabled.
- `plugins stable true` and `plugin_sharing stable true` verify current plugin surfaces are enabled.
- `skill_search stable true` verifies the skill-search feature is enabled.
- `plugin_hooks removed false` must not be treated as the active hook contract; the v0.2 design relies on the current general `hooks` contract and separate acceptance tests for plugin-bundled hook behavior.
- feature-flag presence alone does not prove every lifecycle event or payload contract. Those remain integration-test obligations.

## 6. Evidence conclusions

This raw capture directly supports these v0.2 assumptions for Codex CLI 0.147.0:

1. `codex plugin` is the working CLI family.
2. plugin listing returns structured installed/enabled state.
3. marketplace listing works through the CLI.
4. marketplace registration explicitly accepts local paths and Git sources.
5. hooks, multi-agent, plugins, and skill search are stable/enabled features in this build.

It does **not** by itself prove:

- `.codex-plugin/plugin.json` ingestion for our fixture
- `hooks/hooks.json` execution from our plugin
- individual hook payload contracts
- custom `.codex/agents/*.toml` spawn behavior
- `/plugins` interactive discovery
- Codex Desktop 0.152.0 compatibility

Those remain acceptance gates in the v0.2 specification.

## 7. Privacy/sanitization note

Redacted from the public transcript:

- local username
- user/cache filesystem roots
- complete installed-plugin inventory
- volatile bundled marketplace paths

No auth tokens, MCP credentials, session data, or secret values were included in the supplied capture.
