# Native Plugin Acceptance Evidence Template

Use this template only after running `scripts/acceptance/plugin_smoke.py` against a real Codex binary. Do not copy the raw JSON artifact into the public repository before sanitization review.

## Test identity

- Date:
- OS:
- Codex binary/runtime:
- Codex version:
- Repository commit SHA:
- Plugin version:
- Marketplace name:

## Isolation

- Disposable `CODEX_HOME` used: PASS / FAIL
- Operator's normal Codex profile modified: NO / YES
- Temporary Codex home removed after run: PASS / FAIL

## Marketplace registration

Command family:

```text
codex plugin marketplace add <repo-root> --json
codex plugin marketplace list --json
```

- Marketplace add exit code:
- Marketplace present after add: PASS / FAIL
- Relevant sanitized observation:

## Plugin discovery

Command family:

```text
codex plugin list --available --json
```

If the runtime does not support `--available`, record the fallback rather than hiding it.

- Discovery mode:
- Plugin observed before install: installed / available / not-listed
- Relevant sanitized observation:

## Plugin installation

Command family:

```text
codex plugin add codex-engineering-kit@codex-engineering-kit-dev --json
```

- Add exit code:
- Returned plugin name matches: PASS / FAIL
- Returned marketplace name matches: PASS / FAIL
- Auth policy observed, if exposed:

## Final plugin state

Command family:

```text
codex plugin list --json
```

- Plugin present in `installed`: PASS / FAIL
- `installed: true`: PASS / FAIL
- `enabled: true`, if exposed: PASS / FAIL / NOT EXPOSED

## Raw artifact integrity

- Original temporary JSON filename:
- Original temporary JSON SHA-256:
- Raw artifact committed publicly: NO
- Machine-specific paths removed from this summary: YES / NO
- Credentials/auth tokens observed in raw artifact: NO / YES

## Result

- Acceptance result: PASS / FAIL
- Gates proven by this run:
- Gates explicitly NOT proven by this run:
  - hook execution
  - hook trust
  - custom subagent spawning
  - compaction lifecycle
  - Desktop 0.152.0 behavior
  - explicit manifest `hooks` override
  - macOS/Linux behavior
- Unresolved runtime differences:

## Reviewer note

A successful plugin acceptance run proves only the plugin/marketplace boundary on the named Codex runtime and repository commit. It does not automatically promote hook, subagent, cross-platform, performance, security, or feature-parity claims.
