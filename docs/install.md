# CEK managed lifecycle

The v1 managed path supports exactly Codex CLI 0.153.0 and Python 3.11+. Run all commands from the CEK repository root and pass the same target project each time.

```text
python scripts/cek_lifecycle.py install --project <project-root>
python scripts/cek_lifecycle.py verify --project <project-root>
python scripts/cek_lifecycle.py update --project <project-root>
python scripts/cek_lifecycle.py uninstall --project <project-root>
python scripts/cek_lifecycle.py verify-clean --project <project-root>
```

Use `--codex-home <path>` only when intentionally managing a non-default Codex profile. The lifecycle never copies `auth.json`, credentials, normal-profile configuration, or user-private skills.

## Ownership contract

| Class | Paths | Mutation rule |
| --- | --- | --- |
| CEK-owned global state | `$CODEX_HOME/codex-engineering-kit.install.json` | Created atomically after a successful install; update requires its exact CEK identity; uninstall removes it only after managed cleanup succeeds. |
| Codex-owned plugin state/cache | Codex CLI marketplace, plugin registry, and returned `plugins/cache/.../codex-engineering-kit/<version>` path | Mutated only through `codex plugin` commands. CEK verifies the returned cache stays below the selected `CODEX_HOME` and hashes the manifest, hook manifest, and every shipped skill entrypoint. CEK does not recursively delete cache paths itself. |
| CEK-owned project asset | `<project>/.codex/agents/reviewer.toml` plus `<project>/.codex/codex-engineering-kit.install.json` | Provisioned only when absent. Update requires the recorded reviewer hash. Uninstall removes the reviewer only while that hash still matches. |
| User-owned/pre-existing | Existing reviewer, other agents, project files, Codex profile files, and unrelated marketplace entries | Never overwritten or deleted. A reviewer conflict or CEK marketplace name bound to another checkout fails closed. A user-modified managed reviewer is preserved on uninstall. |
| Local runtime/evidence | `.codex-kit/` | Ignored local state governed by its individual schema; it is not installed or removed by this lifecycle. |

Install records whether it added the CEK marketplace. Uninstall removes that marketplace only when the record says CEK added it; a same-root marketplace that predated the managed install survives. Incomplete or malformed ownership state stops destructive cleanup and requires manual inspection.

## Support boundary

The native plugin packages eight plugin-native skills and default `hooks/hooks.json`; lifecycle verification proves the installed cache matches those shipped files. It does not promote Codex CLI 0.153.0 interactive skill discovery beyond its existing `NOT_RUN` classification.

The provisioned reviewer is a Codex-native project-local role. Plugin installation does not register custom agent roles on CLI 0.153.0, so plugin-native custom agents remain unsupported/deferred. Hooks are guardrails, not a sandbox. No Codex Desktop behavior is inferred.

The PowerShell `scripts/install.ps1`, `scripts/update.ps1`, and `scripts/uninstall.ps1` flow remains a separate ownership-aware installer for six core skills. It does not install the native plugin or provision project-local agents.
