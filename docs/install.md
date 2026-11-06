# CEK managed lifecycle

The current managed native path supports exactly Codex CLI 0.155.1 and Python 3.11+ on Windows x64, using the complete official package below. This aligns onboarding with CEK's digest-pinned Code Mode host. Older 0.153.0 lifecycle observations remain historical evidence, not the current installation requirement.

## Pinned public runtime setup (PowerShell)

Requires Windows x64, Python 3.11+, Git and the Windows `tar` utility. Use a new,
user-owned runtime directory. The complete package includes `bin/codex.exe`,
`codex-package.json`, the Code Mode host, command runner, sandbox setup and `rg`.
Do not substitute the single-executable archive or an npm launcher for this
configuration. Do not replace a normal installation or copy an existing profile.

```powershell
$CekRuntime = Join-Path (Get-Location).Path '.codex-kit/local/codex-runtime-0.155.1'
$CekArchive = "$CekRuntime.tar.gz"
if ((Test-Path -LiteralPath $CekRuntime) -or (Test-Path -LiteralPath $CekArchive)) { throw 'Choose new runtime and archive paths; preserve existing files.' }
New-Item -ItemType Directory -Path (Split-Path -Parent $CekRuntime) -Force | Out-Null
Invoke-WebRequest -Uri 'https://github.com/openai/codex/releases/download/rust-v0.155.1/codex-package-x86_64-pc-windows-msvc.tar.gz' -OutFile $CekArchive
if ((Get-FileHash -LiteralPath $CekArchive -Algorithm SHA256).Hash.ToLowerInvariant() -ne 'f45c273b7835c192aaa9cef5b93aa9528966ac7301444632de80a565a9bf14e8') { throw 'Official package digest mismatch' }
New-Item -ItemType Directory -Path $CekRuntime | Out-Null
tar -xzf $CekArchive -C $CekRuntime
if ($LASTEXITCODE -ne 0) { throw 'Complete runtime extraction failed' }
$CekCodex = Join-Path $CekRuntime 'bin/codex.exe'
& $CekCodex --version
if ($LASTEXITCODE -ne 0) { throw 'CLI could not start' }
python -B -m scripts.acceptance.native_host_probe --codex $CekCodex
if ($LASTEXITCODE -ne 0) { throw 'Native runtime identity/capability check failed' }
```

Expected banner: `codex-cli 0.155.1`. The CLI digest is
`eba0f32c976667cb9298efafd98513e823eeda7b576a03ec658bb8be8d336316`;
the host digest is `480da4a9a98b5b54d6656d731fbcc00c73fd4d0fc4b9aaceafc9fbdf08a7d523`.
The checks are enforced by CEK, not accepted from runtime configuration.
The probe executes JavaScript, invokes one bounded diagnostic delegate and
verifies exact canary bytes. It performs no login, model call or Codex shell task.

## Managed installation

Run all commands from the CEK repository root and pass the same project,
runtime and intentionally isolated profile each time. `<project-root>` must exist.
No authentication is needed for installation or the host probe.

```text
python scripts/cek_lifecycle.py install --project <project-root> --codex-home <isolated-profile> --codex <runtime>/bin/codex.exe
python scripts/cek_lifecycle.py verify --project <project-root> --codex-home <isolated-profile> --codex <runtime>/bin/codex.exe
python scripts/cek_lifecycle.py update --project <project-root> --codex-home <isolated-profile> --codex <runtime>/bin/codex.exe
python scripts/cek_lifecycle.py uninstall --project <project-root> --codex-home <isolated-profile> --codex <runtime>/bin/codex.exe
python scripts/cek_lifecycle.py verify-clean --project <project-root> --codex-home <isolated-profile> --codex <runtime>/bin/codex.exe
```

Use `--codex-home <path>` only when intentionally managing a non-default Codex profile. The lifecycle never copies `auth.json`, credentials, normal-profile configuration, or user-private skills.

For direct `plugin list --json` or `debug prompt-input` CLI discovery commands,
set `CODEX_HOME` in that child process to the same isolated profile. A prompt-input
preview demonstrates enumeration, not model execution. Do not substitute an
authenticated historical profile. Model workflows require a separately available,
authorized login and remain NOT_RUN without one.

The public CLI preflights the approved binary/host pair and matching version
before lifecycle writes. An unsupported, modified or incomplete runtime fails
closed. Use the reported reason code; do not disable the guard or self-approve
new hashes. Alternative OS/architecture packages are not claimed by this setup.

## Ownership contract

| Class | Paths | Mutation rule |
| --- | --- | --- |
| CEK-owned global state | `$CODEX_HOME/codex-engineering-kit.install.json` | Created atomically after a successful install; update requires its exact CEK identity; uninstall removes it only after managed cleanup succeeds. |
| Codex-owned plugin state/cache | Codex CLI marketplace, plugin registry, and returned `plugins/cache/.../codex-engineering-kit/<version>` path | Mutated only through `codex plugin` commands. CEK verifies the returned cache stays below the selected `CODEX_HOME` and hashes the manifest, hook manifest, and every shipped skill entrypoint. CEK does not recursively delete cache paths itself. |
| CEK-owned project asset | `<project>/.codex/agents/reviewer.toml` plus `<project>/.codex/codex-engineering-kit.install.json` | Provisioned only when absent. Update requires the recorded reviewer hash. Uninstall removes the reviewer only while that hash still matches. |
| User-owned/pre-existing | Existing reviewer, other agents, project files, Codex profile files, and unrelated marketplace entries | Never overwritten or deleted. A reviewer conflict or CEK marketplace name bound to another checkout fails closed. A user-modified managed reviewer is preserved on uninstall. |
| Local runtime/evidence | `.codex-kit/` | Ignored local state governed by its individual schema; it is not installed or removed by this lifecycle. |

Install records whether it added the CEK marketplace. Uninstall removes that marketplace only when the record says CEK added it; a same-root marketplace that predated the managed install survives. Incomplete or malformed ownership state stops destructive cleanup and requires manual inspection.

Uninstall rechecks the marketplace root immediately before any plugin/marketplace removal and confirms that an owned marketplace actually disappeared before deleting lifecycle state. `verify-clean` also fails closed when the CEK marketplace name remains registered; this makes a surviving user-owned marketplace explicit instead of silently calling the profile clean.

## Support boundary

The native plugin packages eight plugin-native skills and default `hooks/hooks.json`; lifecycle verification proves the installed cache matches those shipped files. The current non-model boundary is installation, plugin enumeration, skill prompt preview and the bounded native-host probe. Model-driven tasks, native reviewer execution and model tool/shell integration are NOT_RUN until genuinely executed.

The provisioned reviewer is a Codex-native project-local role. Its file installation does not prove a distinct reviewer executed. Historical 0.153.0 hook/reviewer/compaction acceptance is not promoted to 0.155.1. Hooks are guardrails, not a sandbox. No Codex Desktop behavior is inferred. See [current and historical boundaries](verification/runtime-compatibility.md).

The PowerShell `scripts/install.ps1`, `scripts/update.ps1`, and `scripts/uninstall.ps1` flow remains a separate ownership-aware installer for six core skills. It does not install the native plugin or provision project-local agents.
