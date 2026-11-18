# Published beta model-driven smoke — 18 November 2026

**Result: PASS for one bounded task, not a general acceptance rate.**

## Exact tested source

- Released source: annotated tag `v1.1.0-beta.1`, resolved commit `e4d9430f23af6a248ee322559c5c5a391f3e3339`.
- Test source: clean detached checkout of that tag, **not** later `main` or PR #6.
- Runtime: Windows x64, PowerShell 7.6.10, complete official Codex CLI 0.155.1, Python 3.14.
- CLI SHA-256: `eba0f32c976667cb9298efafd98513e823eeda7b576a03ec658bb8be8d336316`.
- Native Code Mode host SHA-256: `480da4a9a98b5b54d6656d731fbcc00c73fd4d0fc4b9aaceafc9fbdf08a7d523`.
- Separate disposable `CODEX_HOME` and task fixture; official device login completed by the operator. No credentials were copied or inspected.
- Managed native plugin: `1.1.0-beta.1`. All 10 installed, manifest-listed assets matched their SHA-256 records. Native host diagnostic probe passed independently of model execution.

## What happened

A **single** real `gpt-6-astra` model-driven run (253.761 seconds, exit 0) used the installed orchestrator and verification-loop skills, the existing `tests/fixtures/representative-workflow` task and a native reviewer.

| Evidence | Observed result |
| --- | --- |
| Before edit | Existing unit test failed: division by zero did not raise `ValueError` (RED, native event `item_6`) |
| Edit | One source change in `src/calculator.py`: replace infinity return with `raise ValueError("division by zero")` (`item_8`) |
| After edit | Both unit tests passed (GREEN, `item_9`) |
| Skill use | Installed orchestrator and verification-loop content appeared in the native tool output (`item_4`) |
| Native reviewer | Independent project-local read-only reviewer performed bounded file/diff review; it did **not** rerun tests |
| External check | Separate parent process reran both tests and exact normal-division/exception behavior; PASS |
| Verification | Installed CEK verifier produced a current candidate-bound report; wrong-identity, stale pre-fix GREEN and missing-artifact report candidates were rejected in memory |
| Preservation | Six explicitly protected files, the existing non-source task files, task Git index and HEAD, and source checkout were unchanged |
| Allowed outputs | Only `src/calculator.py` changed among task source files; generated `.codex-kit/verification/latest.json` was the only added task file |

Candidate digest: `11839b49cd82be11f2903f49ada930c43ad3a2b8ab38c99d041eaf944059fb77`.

The CLI `turn.completed` event reported 455,799 input tokens (401,920 cached input tokens) and 2,277 output tokens. These are **runtime event counters**, not verified billing, price or a meaningful average. There was no Plain Codex baseline.

## Important caveats

- The first combined native command ended with exit 1 due to a subsequent noncritical file search, **after** both skill files had been read. Skill reads are supported by the command's contents, not by a blanket claim that every native command succeeded.
- The official CLI warned that skill descriptions were shortened to fit the context budget. Per-project isolation of inherited user-global skills remains unresolved.
- A **redundant** lifecycle `verify` later stalled on a Codex `plugin list --json` child process; it was stopped without changing the successful model attempt. Initial installation and verification, manifest integrity, native host probe and the model workflow had succeeded.
- Code Mode was marked under development by this pinned CLI. Workspace-write, restricted network and unelevated Windows sandbox were requested/observed at the CLI policy level; OS-token enforcement was not independently attested.
- This exercise involved one simple, deterministic calculator bug. It does **not** establish cross-platform runtime support, general reliability, interruption recovery, token/cost advantage, or superiority over stock Codex or ECC.

## Evidence and privacy

The operator retained the exact local model-event transcript, session metadata, independent test outputs, protected-file hashes and candidate-integrity verification in an **unpublished, disposable evidence directory**. They were independently inspected for this record, but the raw logs and authenticated `CODEX_HOME` are **not public artifacts** and must never be copied into the repository.

This note is a sanitized, evidence-grounded summary, not a reproducible transcript and not an authoritative benchmark. See [beta release notes](../../release/v1.1-beta.1.md), the [quickstart](../../quickstart.md), and the separate [earlier 1.0.0 workflow summary](cek-real-workflow-20261106.json) for their respective scopes.
