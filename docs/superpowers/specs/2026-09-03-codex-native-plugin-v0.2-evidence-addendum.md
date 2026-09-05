# Codex Engineering Kit v0.2 — Raw Evidence Gate Addendum

Date: 2026-09-03
Applies to: `2026-09-03-codex-native-plugin-v0.2-final-design-v2.md`

This addendum closes the **raw local evidence capture** prerequisite in Section 5 of the final v0.2 design. It does not close runtime acceptance gates for plugin ingestion, hook execution, subagent spawning, Desktop 0.152.0 behavior, or interactive plugin discovery.

## Evidence artifact

Sanitized public transcript:

```text
docs/research/evidence/codex-cli-0.147.0-raw-evidence-sanitized.md
```

SHA-256 of the original uncommitted local capture:

```text
73fe8e5030ff22b1246b9896dc1eca7a299b79d4a79296bd15c6c0f74ab4634b
```

## Raw commands captured

```text
codex --version
codex plugin list --json
codex plugin marketplace list --json
codex plugin marketplace add --help
codex features list
```

## Verified conclusions for terminal Codex CLI 0.147.0

- effective CLI reports `codex-cli 0.147.0`
- `codex plugin list --json` returns structured installed/enabled plugin state
- `codex plugin marketplace list --json` returns structured marketplace registrations
- `codex plugin marketplace add` accepts a local path and Git marketplace sources
- `hooks` is `stable true`
- `multi_agent` is `stable true`
- `plugins` is `stable true`
- `plugin_sharing` is `stable true`
- `skill_search` is `stable true`
- legacy `plugin_hooks` is shown as removed and is not used as the v0.2 contract

## Sanitization

The public transcript intentionally omits:

- local username
- user/cache filesystem roots
- complete installed-plugin inventory
- volatile bundled marketplace paths

No auth token, MCP credential, private session content, or secret value was present in the supplied capture.

## Gate status

`RAW-CLI-EVIDENCE-0.147.0`: **SATISFIED**

Still open:

- plugin fixture ingestion
- plugin hook trust and execution
- individual hook payload/ordering contracts
- custom agent load/spawn
- interactive `/plugins` acceptance
- Codex Desktop 0.152.0 acceptance
- manifest `hooks` override compatibility

The implementation plan may begin after owner approval of the final design; these remaining items are implementation/acceptance gates, not missing pre-design evidence.
