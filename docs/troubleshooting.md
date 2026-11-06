# Native setup and workflow troubleshooting

Keep the failed command, exit code and non-sensitive output. Do not paste tokens,
profile contents or private keys into an issue. Use [install.md](install.md) and
the [quickstart](quickstart.md) for the exact supported setup.

| Symptom | Evidence to check | Supported next action |
| --- | --- | --- |
| `CODE_MODE_RUNTIME_UNSUPPORTED` or package digest failure | CLI/package version and the published archive/CLI/host hashes | Use the complete verified official 0.155.1 Windows x64 package. Do not approve new hashes or disable the guard. |
| Missing host or incomplete package | `bin/codex.exe`, host, metadata, command runner, sandbox setup and rg | Extract the complete package to a new owned directory. A launcher or lone executable is insufficient. |
| `CEK_SOURCE_PROFILE_OVERLAP` | Source and profile containment in either direction | Use a fresh public source checkout and a separate profile/runtime/task location. Preserve a legacy nested profile; do not migrate credentials or bypass the check. |
| `CODEX_HOME ... path does not exist` | Selected isolated profile path | Create that new empty directory before CLI calls. Do not copy another profile. |
| `Could not determine home directory` in a stripped helper environment | Normal Windows `USERPROFILE`/home variables | Use an ordinary authorized PowerShell environment. `CODEX_HOME` does not replace every OS home lookup. Do not inject credentials. |
| Marketplace points elsewhere, unmanaged CEK already installed or unowned reviewer | Ownership record and named public installation paths | Preserve existing files. Use a new empty isolated profile/project; managed update is only for an already owned installation. No implicit adoption or overwrite. |
| Unrelated skills despite isolated profile | Actual model context's skill roots and entry list | A separate `CODEX_HOME` still loads user-global `.agents/skills`. Record the scope; no complete isolation claim. Do not automatically delete skills or change account plugins. |
| Skill descriptions shortened | Actual session warning and visible entries | Shortened descriptions do not mean skills are omitted. The observed run had 8 CEK, 143 user-global and 5 system entries; another machine can differ. |
| `--sandbox` conflicts with `--approve-for-me` | CLI argument error before a model turn | Use `--approve-for-me` alone for reviewed workspace-write, retaining the Windows/network options. No model task occurred if parsing failed. |
| Effective read-only permissions or denied approval | Actual turn's policy and tool result | Stop. Request the supported operator policy change; never bypass managed controls. |
| PowerShell CLM rejects a static .NET operation | Exact failing operation and `LanguageMode` | Use permitted filesystem cmdlets where equivalent. Do not disable CLM or elevate automatically. |
| Model-list refresh timeout or usage exhaustion | Actual turn start/completion and terminal errors | A warning alone does not prove task failure; the retained run still completed. On a terminal model/usage failure, preserve evidence and stop. |
| Missing host, malformed response, timeout or artifact mismatch during execution | Structured `NativeExecutionError.diagnostic.to_dict()` | Follow its bounded operator action. Do not convert process exit zero into workflow success. |
| Stale GREEN or `VERIFICATION_STALE_OR_ARTIFACT_MISSING` | Current relevant-file manifest vs the tested candidate | Reject the old report. Verify the final candidate; HEAD alone is insufficient. |

The [integrity guide](verification/product-integrity.md) documents the manifest's
input/exclusion scope, time-of-check boundary, local recovery limits and native
error classes. The beta does not certify adversarial concurrent filesystem access,
arbitrary exactly-once external effects or machine-wide absence of writes.
