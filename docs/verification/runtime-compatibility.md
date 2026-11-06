# Current native runtime compatibility

The public managed native configuration is the complete official Codex CLI
**0.155.1 Windows x64** package described in [install.md](../install.md).
`runtime/assurance/native_host.py:RUNTIME_VERSION` is shared by the installer
and native guard; `release_contracts/compatibility.json:currentProductRuntime`
declares the exact release archive, CLI and host digests. Regression tests check
that this declaration and both public installation entry points agree.

## Root cause

The previous public installer accepted only CLI 0.153.0. The actual official npm
installation reported that version, had its host at the supported adjacent
location, and passed plugin installation. Its CLI digest was
`0f8ed9678bca539aa6517adb0c8d50ad9a94ff5df4d21e149ae700d219fff69d`.
The native guard rejected that digest as `CODE_MODE_RUNTIME_UNSUPPORTED`.
This was an incompatible installation requirement, not proof that the host was
missing. Neither a new unverified digest nor a guard exclusion was added.

The selected complete 0.155.1 release uses the existing approved CLI/host pair:

| Artifact | SHA-256 |
| --- | --- |
| Complete Windows x64 `.tar.gz` | `f45c273b7835c192aaa9cef5b93aa9528966ac7301444632de80a565a9bf14e8` |
| CLI | `eba0f32c976667cb9298efafd98513e823eeda7b576a03ec658bb8be8d336316` |
| Code Mode host | `480da4a9a98b5b54d6656d731fbcc00c73fd4d0fc4b9aaceafc9fbdf08a7d523` |

Publisher provenance: [OpenAI release rust-v0.155.1](https://github.com/openai/codex/releases/tag/rust-v0.155.1).
Use the complete `codex-package-x86_64-pc-windows-msvc.tar.gz`, not the similarly
named single-executable archive. No global runtime or credentials need be changed.

## Enforcement and evidence boundaries

The public lifecycle CLI requires the native preflight and all six official
package files before installation mutations. Their digests come from the
independently verified release archive. The guard rejects unsafe paths,
hardlinks, unknown CLI digests,
version disagreements and missing/modified hosts. Only a digest-approved CLI
is queried for its version, using a temporary unauthenticated home and a minimal
environment. The existing host handshake, bounded JavaScript/tool delegate,
exact artifact verification and post-probe host hash checks remain in force.

Installation verifies packaged files and provisions the project-local reviewer.
CLI prompt-input enumeration can show the eight required skills without a model
call. The host probe proves JavaScript and one bounded diagnostic delegate are
callable; it does not test the model's real shell tool or task reasoning.

A separately authenticated run on source commit
`e5dc24941f9f3b858f1534d8404598579c5d8564` and package 1.0.0 completed **one**
representative bug fix using `gpt-6-astra`: installed skill reads, native shell,
RED/GREEN, a distinct native reviewer and independent candidate/artifact checks.
See the [sanitized record](../research/evidence/cek-real-workflow-20261106.json).
The unpublished beta changes packaging/docs, not the workflow engine; no new
model execution on the beta artifact is claimed.

Authenticated hook/compaction acceptance, model interruption recovery, other
agent roles, other tasks and other OS/architecture native runtimes remain
**NOT_RUN** on this configuration. Global skill inheritance remains observable;
a separate CODEX_HOME is not complete context isolation.
Historical 0.147.0/0.153.0 and Desktop 0.152.0 compatibility rows and evidence are
retained unchanged. No historical result is promoted to the new configuration.
The current candidate package is 1.1.0-beta.1; it has not been published. Historical evidence is not a blanket v1.1 release claim.
