# Codex CLI 0.147.0 Native Plugin Acceptance Evidence

Date: 2026-09-03

## Test identity

- OS: Windows operator workstation
- Codex runtime: `codex-cli 0.147.0`
- Repository commit: `419d9e4b6bfd8929cca90b03f68bd7b72f5a3715`
- Plugin: `codex-engineering-kit`
- Plugin version: `0.2.0-alpha.1`
- Marketplace: `codex-engineering-kit-dev`

## Isolation

The acceptance runner used a disposable `CODEX_HOME` and did not reuse the operator's normal Codex profile.

Observed checks:

- disposable Codex home used: PASS
- marketplace registered: PASS
- plugin discovered before install: PASS (`available`)
- plugin add returned expected plugin name: PASS
- plugin add returned expected marketplace: PASS
- final plugin state `installed: true`: PASS
- final plugin state `enabled: true`: PASS
- disposable Codex home removed after run: PASS

## Command boundary proven

The real Codex CLI successfully completed this sequence:

```text
codex --version
codex plugin marketplace add <repo-root> --json
codex plugin marketplace list --json
codex plugin list --available --json
codex plugin add codex-engineering-kit@codex-engineering-kit-dev --json
codex plugin list --json
```

The plugin was visible as `available` before installation and moved to `installed` after `codex plugin add`.

## Sanitized observations

Marketplace registration returned the expected marketplace name. Machine-specific install roots were redacted by the acceptance runner.

Pre-install discovery exposed:

```text
name: codex-engineering-kit
marketplaceName: codex-engineering-kit-dev
version: 0.2.0-alpha.1
installed: false
enabled: false
installPolicy: AVAILABLE
authPolicy: ON_USE
```

Final plugin state exposed:

```text
name: codex-engineering-kit
marketplaceName: codex-engineering-kit-dev
version: 0.2.0-alpha.1
installed: true
enabled: true
installPolicy: AVAILABLE
authPolicy: ON_USE
```

## Raw artifact integrity

- Raw temporary artifact: `cek-plugin-acceptance-0.147.0.json`
- SHA-256: `AC4B88078C73F6B1B0BB34B49D8C932E6B13596BF422BD7A7A17FDC9A83355AD`
- Raw artifact committed publicly: NO
- Machine-specific paths removed from this summary: YES
- Credentials/auth tokens observed in the shared acceptance output: NO

## Result

Acceptance result: **PASS**

This run proves only the native plugin + repo-local marketplace boundary on Codex CLI `0.147.0` at repository commit `419d9e4b6bfd8929cca90b03f68bd7b72f5a3715`.

Gates proven:

- `.codex-plugin/plugin.json` is accepted through the real local marketplace/install path on CLI 0.147.0.
- `.agents/plugins/marketplace.json` is accepted by the real CLI marketplace path.
- the plugin is discoverable through `codex plugin list --available --json`.
- `codex plugin add` installs and enables the plugin in a disposable Codex home.

Gates explicitly **not** proven by this run:

- native hook execution or hook trust behavior
- custom subagent spawning
- compaction lifecycle
- Desktop bundled Codex 0.152.0 behavior
- explicit plugin manifest `hooks` override
- macOS/Linux real-Codex behavior
- performance/context-efficiency claims

## Windows runner regression evidence

During this checkpoint, the acceptance runner initially failed on Windows with `FileNotFoundError: [WinError 2]` while launching a PATH-resolved Codex command. The failure was reproduced in Windows CI using a `.cmd` shim, then fixed by resolving the executable from the child process `PATH` before `subprocess.run(..., shell=False)`.

The fix commit is `419d9e4b6bfd8929cca90b03f68bd7b72f5a3715`; GitHub Actions run `33745691023` completed successfully after the fix, including the Windows executable-resolution regression test and the pre-existing installer, verification, learning, and MCP contracts.
