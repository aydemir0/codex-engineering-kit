# CEK v1 WS7 clean-install evidence

Date: 2026-09-12

WS6 baseline: `29bee4282ea21785d618dc477e984a3f44afc8d7`

Source worktree HEAD: `0da70a7618592e26aeeba422d899f60dfe8a50e7`

Hardened disposable candidate snapshot: `4f4c7e130916b1370d86fd9fb3a4785d2c907c69`

Runtime: Codex CLI 0.153.0

## Contract

The managed path owns two explicit manifests and one project-local asset. Codex CLI owns the plugin registry and cache. CEK verifies that the CLI-returned cache remains below the selected disposable `CODEX_HOME` and that the cached plugin manifest, default hook manifest, and all eight shipped skill entrypoints match the source hashes. Existing or modified user assets are not owned by filename coincidence.

The provisioned `.codex/agents/reviewer.toml` is a Codex-native project-local role. Plugin installation does not register custom agent roles on CLI 0.153.0; plugin-native custom agents remain unsupported/deferred. Installed cache verification is not promoted to interactive skill-discovery evidence, which remains `NOT_RUN`. Hooks remain guardrails, not a sandbox, and no Desktop behavior is inferred.

The PowerShell installer remains a separate ownership-aware delivery path for six core skills. It does not install the native plugin or provision project-local agents.

## Disposable acceptance

The campaign ran `python -B -m scripts.acceptance.clean_install` against the exact candidate in one repository-external temporary root. It did not copy auth, credentials, normal-profile configuration, user-private skills, or unrelated repository files into a Codex profile.

Results:

- clean install and consolidated verification: PASS;
- cached plugin manifest, eight skill entrypoints, and `hooks/hooks.json` hash verification: PASS;
- project-local reviewer source/destination equality: PASS;
- pre-existing reviewer conflict stopped before plugin mutation: PASS;
- deterministic `0.2.0-alpha.0` prior-install fixture to `0.2.0-alpha.1` update and second verification: PASS;
- uninstall and verify-clean: PASS;
- project and profile sentinels survived byte-for-byte: PASS;
- reinstall verification: PASS;
- disposable roots remaining after completion: 0.

The machine-readable sanitized result is `docs/research/evidence/codex-v1-ws7-clean-install.json`.

The final acceptance snapshot includes marketplace-rebinding and same-name cross-marketplace update hardening. Focused RED→GREEN regression tests proved that uninstall refuses a rebinding before plugin mutation, refuses to remove lifecycle state when marketplace removal is not confirmed, and refuses update when the existing plugin is bound to another marketplace. The snapshot is a repository-external disposable Git commit of the working tree because the local worktree's Git metadata was unavailable for a second commit; this is recorded rather than presented as the branch HEAD.

## Final verification gates

- focused lifecycle, docs, compatibility, security, state, and hook regressions: PASS (59 tests; lifecycle 12 tests, docs 3 tests);
- full Python regression suite: PASS (246 tests);
- PowerShell install, verify, learning, and MCP suites: PASS;
- content validation, 13-claim/13-surface release validation, compile checks, and `git diff --check`: PASS;
- disposable snapshot cleanup: PASS (zero snapshot/output residues);
- independent final review: PASS after the ownership hardening rerun, with no material findings.

## Preserved boundaries

The frozen WS6 dataset and methodology were not changed. The recorded result remains 45 authenticated runs: A 15/15 PASS, B 15/15 PASS, C 4/15 PASS, and 34 PASS / 11 retained FAIL, with no retry or replacement and no superiority claim. The CLI 0.153.0 unauthorized connector startup warning remains documented and is not reinterpreted.

## Remaining closure gates

Repository-wide regressions, PowerShell suites, content/release validation, and independent final review are recorded only after fresh execution. This document does not claim WS7 closure before those gates pass.
