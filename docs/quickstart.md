# Windows public beta quickstart

The [v1.1.0-beta.1](https://github.com/aydemir0/codex-engineering-kit/releases/tag/v1.1.0-beta.1) pre-release uses the complete official
Codex CLI 0.155.1 Windows x64 package, PowerShell 7+, Python 3.11+ and Git.
The prior main-based one-task observation is linked in the [beta notes](release/v1.1-beta.1.md).

## 1. Prepare the runtime and an empty profile

Launch a fresh PowerShell 7 session with `pwsh`. Before running any
installation commands, check `$PSVersionTable.PSVersion` and continue only
if the major version is 7 or higher.

Clone the published beta with `git clone --branch v1.1.0-beta.1 https://github.com/aydemir0/codex-engineering-kit.git`.
In the checkout, `git rev-parse HEAD` should print
`e4d9430f23af6a248ee322559c5c5a391f3e3339`.
From its repository root, follow the exact download, archive checksum and
Windows `tar` commands in [install.md](install.md). Keep `$CekCodex` pointing to
that package's `bin/codex.exe`.

Choose new paths outside the source checkout. The local marketplace snapshots
its source; nesting CODEX_HOME under that source would copy live cache state into
itself. CEK rejects overlapping source/profile roots. Keep the source checkout
free of private or ignored local state. These commands refuse existing directories:

```powershell
$CekRepo = (Get-Location).Path
$CekLocal = Join-Path $env:TEMP 'cek-beta-first-use'
if (Test-Path -LiteralPath $CekLocal) { throw 'Choose a new disposable directory; preserve existing files.' }
New-Item -ItemType Directory -Path $CekLocal | Out-Null
$CekProfile = Join-Path $CekLocal 'profile'
$CekProject = Join-Path $CekLocal 'task'
New-Item -ItemType Directory -Path $CekProfile | Out-Null
Copy-Item -LiteralPath (Join-Path $CekRepo 'tests/fixtures/representative-workflow') -Destination $CekProject -Recurse
Set-Content -LiteralPath (Join-Path $CekProject 'foreign-owner.txt') -Value 'PRESERVE_THIS_FILE' -Encoding ascii
$env:CODEX_HOME = $CekProfile
python -B scripts/cek_lifecycle.py install --project $CekProject --codex-home $CekProfile --codex $CekCodex
if ($LASTEXITCODE -ne 0) { throw 'Installation failed; retain the output and stop.' }
python -B scripts/cek_lifecycle.py verify --project $CekProject --codex-home $CekProfile --codex $CekCodex
if ($LASTEXITCODE -ne 0) { throw 'Installed ownership/content check failed.' }
& $CekCodex plugin list --json
```

Expect CEK `1.1.0-beta.1` and eight shipped skill files. Installation,
plugin enumeration and skill preview are different from actual skill execution.
A new `CODEX_HOME` does not isolate user-global `.agents/skills`.

## 2. No-login demonstration

From `$CekRepo`, the following creates disposable fixtures, tests candidate-bound
verification/recovery/diagnostics and makes **no model calls**:

```powershell
python -B -m scripts.demo_product_integrity --output (Join-Path $CekLocal 'integrity-demo.json')
if ($LASTEXITCODE -ne 0) { throw 'Local deterministic demo failed.' }
```

The intentionally buggy task fixture remains unchanged by this separate demo.
A host-only probe is also available in `install.md`; it is not a model workflow.

## 3. Optional, explicitly authorized real task

Initialize only this disposable task's Git repository; these commands do not
change global Git configuration or access signing keys:

```powershell
git -C $CekProject init -b main
if ($LASTEXITCODE -ne 0) { throw 'Fixture Git initialization failed.' }
git -C $CekProject add -- .
if ($LASTEXITCODE -ne 0) { throw 'Fixture staging failed.' }
git -C $CekProject -c user.name='CEK Fixture' -c user.email='fixture@example.invalid' -c commit.gpgsign=false commit --no-gpg-sign -m 'Disposable task baseline'
if ($LASTEXITCODE -ne 0) { throw 'Fixture baseline failed.' }
```

Never substitute a user's real project. Run `& $CekCodex login status`. If this profile is unauthenticated, stop before
model execution. You may personally choose the official `login --device-auth`
flow for this profile; never copy credentials or authenticate automatically.
No login is needed for the checks in sections 1-2.

Review the task and supplied CEK skill files. Make the installed verifier
available without copying any files or credentials:

```powershell
$CekOwnership = Get-Content -LiteralPath (Join-Path $CekProfile 'codex-engineering-kit.install.json') -Raw | ConvertFrom-Json
$env:PYTHONPATH = $CekOwnership.installedPath
$env:PYTHONDONTWRITEBYTECODE = '1'
```

Then, only with model use authorized:

```powershell
$CekTaskPrompt = 'Use the installed CEK orchestrator and verification-loop. Read task.md and the installed skill files. Run the existing tests to reproduce RED before editing. Change only src/calculator.py as task.md requires, never the tests or sentinel. Run GREEN, request the provisioned read-only reviewer if supported, and run the installed verification engine. Report actual commands, effective permissions and evidence; stop on policy denial. No Git staging/commits, network tasks or credential access.'
& $CekCodex exec --cd $CekProject --enable code_mode --approve-for-me -c 'windows.sandbox="unelevated"' -c 'sandbox_workspace_write.network_access=false' --json $CekTaskPrompt
```

`--approve-for-me` already selects workspace-write: do **not** combine it with
`--sandbox`. It retains automatic approval review; no bypass flags are needed.
Confirm the actual runtime reports the intended permissions. This path requests
the Windows unelevated sandbox; the recorded workflow did not separately attest
the OS token. Code Mode is marked under development by the pinned CLI.

Use `python -B -m unittest discover -s tests -v` inside `$CekProject` to check RED
and GREEN. For the installed verifier, set `PYTHONPATH` only to the CEK
`installedPath` reported by its ownership record, then run
`python -B -m verification.cli --project $CekProject --json`.
Use a separate process to rerun tests, inspect `git diff`, compare protected file
hashes and recheck the report's candidate identity before accepting the result.
An exit code alone is insufficient. Preserve failures; do not retry for a nicer result.

This fixture demonstrates mechanics, not broad engineering quality. Build,
typecheck and lint can be SKIPPED because the fixture has no corresponding setup.
See [troubleshooting](troubleshooting.md) before changing any security setting.
